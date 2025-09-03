# app/api/v1/chat_service.py
from fastapi import HTTPException, status
from app.core.models.pydantic.chat import SearchAndAnswerRequestDto, ChatHistoryResponseDto, SessionClearResponseDto
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from app.core.qdrant.qdrant_client import searchChunksOllama
from app.core.llm.llm import (
    askHuggingFaceLLM, 
    askHuggingFaceLLMWithMemory, 
    get_conversation_history, 
    clear_conversation_memory
)
from app.core.llm.memory_utils import get_all_sessions, get_session_message_count
from typing import Optional
import uuid

class ChatService:
    @staticmethod
    async def handleSearchAndAnswer(
        request: SearchAndAnswerRequestDto, 
        use_memory: bool = True
    ) -> dict:
        """Handle search and answer with optional memory."""
        try:
            # Get project index details
            projectIndexDetails = await VectorIndexRepository.findOneByClause(
                {"projectId": request.projectId}
            )
            if not projectIndexDetails:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Project index not found"
                )

            all_hits = []

            # Search logic - same as your original
            if request.categoryId:
                namespaceDetails = await VectorNamespaceRepository.findOneByClause(
                    {"id": request.categoryId}
                )
                if not namespaceDetails:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        detail="Namespace not found"
                    )

                results = searchChunksOllama(
                    collection_name=projectIndexDetails.indexName,
                    namespace=namespaceDetails.name,
                    query=request.query
                )
                all_hits.extend(results)
            else:
                namespaces = await VectorNamespaceRepository.findAllByClause(
                    {"indexId": projectIndexDetails.id}
                )
                for ns in namespaces:
                    results = searchChunksOllama(
                        collection_name=projectIndexDetails.indexName,
                        namespace=ns.name,
                        query=request.query
                    )
                    all_hits.extend(results)

            # Transform results
            formatted_hits = [{"fields": hit.payload} for hit in all_hits]

            # Generate session ID if not provided and memory is requested
            session_id = request.sessionId
            if use_memory and not session_id:
                session_id = str(uuid.uuid4())

            # Choose LLM function based on memory requirement
            if use_memory and session_id:
                answer, session_id = askHuggingFaceLLMWithMemory(
                    question=request.query,
                    context_chunks=formatted_hits,
                    session_id=session_id
                )
                return {
                    "answer": answer,
                    "sessionId": session_id,
                    "memoryEnabled": True,
                    "contextChunksCount": len(formatted_hits)
                }
            else:
                # Use original function without memory
                answer = askHuggingFaceLLM(request.query, formatted_hits)
                return {
                    "answer": answer,
                    "memoryEnabled": False,
                    "contextChunksCount": len(formatted_hits)
                }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Internal server error: {str(e)}"
            )

    @staticmethod
    def clear_session(session_id: str) -> SessionClearResponseDto:
        """Clear conversation memory for a session."""
        success = clear_conversation_memory(session_id)
        return SessionClearResponseDto(
            sessionId=session_id,
            message=f"Session {'cleared successfully' if success else 'not found or already empty'}",
            success=success
        )
    
    @staticmethod
    def get_session_history(session_id: str) -> ChatHistoryResponseDto:
        """Get conversation history for a session."""
        history = get_conversation_history(session_id)
        return ChatHistoryResponseDto(
            sessionId=session_id,
            history=history
        )
    
    @staticmethod
    def get_all_active_sessions() -> dict:
        """Get all active sessions with metadata."""
        sessions = get_all_sessions()
        session_info = []
        
        for session_id in sessions:
            message_count = get_session_message_count(session_id)
            session_info.append({
                "sessionId": session_id,
                "messageCount": message_count
            })
        
        return {
            "totalSessions": len(sessions),
            "sessions": session_info
        }

    @staticmethod
    def health_check() -> dict:
        """Health check endpoint for the chat service."""
        return {
            "status": "healthy",
            "service": "ChatService",
            "features": {
                "memoryEnabled": True,
                "vectorSearch": True,
                "multipleNamespaces": True,
                "sessionManagement": True
            }
        }
