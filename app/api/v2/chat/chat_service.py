# app/api/v1/chat_service.py
from fastapi import HTTPException, status
from pypika_tortoise.enums import Order
from app.core.models.pydantic.chat import SearchAndAnswerRequestDto, ChatHistoryResponseDto, SessionClearResponseDto, UserChatHistoryDto
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from app.core.repository.chat_repository import ChatRepository
from app.core.qdrant.qdrant_client import searchChunksOllama
from app.core.llm.llm import (
    askHuggingFaceLLM, 
    askHuggingFaceLLMWithMemory, 
    get_conversation_history, 
    clear_conversation_memory
)
from app.core.llm.memory_utils import get_all_sessions, get_session_message_count
from typing import Optional
from app.utils.common import getPaginationResponse
import uuid

class ChatService:
    @staticmethod
    async def handleSearchAndAnswer(
        request: SearchAndAnswerRequestDto, 
        use_memory: bool = True,
        currentUser: Optional[dict] = None
    ) -> dict:
        """Handle search and answer with optional memory."""
        try:
            chatDetails = await ChatRepository.findOneByClause({
                "userId": currentUser.get("userId"),
                "sessionId": request.sessionId
            })

            if chatDetails and chatDetails.chatHistory:
                chatHistory = chatDetails.chatHistory.copy()
            else:
                chatHistory = []
            
            # Get project index details
            projectId = chatDetails.projectId if request.sessionId else request.projectId
            categoryId = chatDetails.categoryId if request.sessionId else request.categoryId
            projectIndexDetails = await VectorIndexRepository.findOneByClause(
                {"projectId": projectId}
            )
            if not projectIndexDetails:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Project index not found"
                )

            all_hits = []

            # Search logic - same as your original
            if categoryId:
                namespaceDetails = await VectorNamespaceRepository.findOneByClause(
                    {"id": categoryId}
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

            formatted_hits = [{"fields": hit.payload} for hit in all_hits]
            session_id = request.sessionId
            if use_memory and not session_id:
                session_id = str(uuid.uuid4())

            if use_memory and session_id:
                answer, session_id = askHuggingFaceLLMWithMemory(
                    question=request.query,
                    context_chunks=formatted_hits,
                    session_id=session_id
                )
                chatHistory.extend([
                        {"user": request.query},
                        {"assistant": answer}
                ])

                if chatDetails:
                    await ChatRepository.updateByClause(
                        {"id": chatDetails.id},
                        chatHistory=chatHistory
                    )
                else:
                    await ChatRepository.create({
                        "projectId": projectId,
                        "categoryId": categoryId,
                        "userId": currentUser.get("userId"),
                        "sessionId": session_id if session_id else "",
                        "chatHistory": chatHistory
                    })
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
    @staticmethod
    async def getUserChatHistory(currentUser: dict, page: int, limit: int) -> dict:
        """Get all conversation histories for the user."""
        try: 
            offset = (page -1 ) * limit
            chatDetails, totalCount = await ChatRepository.findAllByClause(
                {
                    "userId": currentUser.get("userId")
                },
                offset=offset,
                limit=limit,
            )
            result: list[UserChatHistoryDto] = []
            for chat in chatDetails:
                chatTitle = None
                # Find the first user message in chatHistory
                for message in chat.chatHistory:
                    if "user" in message and isinstance(message["user"], str):
                        # Take first 5 words of the user message as chatTitle
                        chatTitle = " ".join(message["user"].split()[:5])
                        break

                result.append(
                    UserChatHistoryDto(
                        ProjectId=chat.projectId,
                        categoryId=chat.categoryId,
                        sessionId=chat.sessionId,
                        chatTitle=chatTitle,
                        chatHistory=chat.chatHistory
                    )
                )

            return {
                "data": result,
                "pagination": getPaginationResponse(totalCount, limit, page, len(chatDetails)),
            
        }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Internal server error: {str(e)}"
            )

    @staticmethod
    async def getUserChatBySessionId(currentUser: dict, session_id: str) -> list:
        """Get all conversation histories for the user."""
        try:
            chatDetails = await ChatRepository.findAllByClause(
                {
                    "userId": currentUser.get("userId"),
                    "sessionId": session_id
                }
            )
            result: list[UserChatHistoryDto] = []
            for chat in chatDetails:
                result.append(
                    UserChatHistoryDto(
                        ProjectId=chat.projectId,
                        categoryId=chat.categoryId,
                        sessionId=chat.sessionId,
                        chatHistory=chat.chatHistory
                    )
                )
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Internal server error: {str(e)}"
            )


