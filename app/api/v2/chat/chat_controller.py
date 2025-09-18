# app/api/v1/chat.py
from fastapi import APIRouter, status, Query, Path, Depends
from .chat_service import ChatService
from app.core.models.pydantic.chat import SearchAndAnswerRequestDto, ChatHistoryResponseDto, SessionClearResponseDto, UserChatHistoryDto
from typing import Optional, Dict, List
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description="Search and answer with optional conversation memory",
    response_model=dict
)
async def search_and_answer(
    request: SearchAndAnswerRequestDto,
    use_memory: bool = Query(True, description="Enable conversation memory"),
    currentUser: Dict = Depends(get_current_user)
):
    """
    Search for relevant content and generate an answer.

    - **use_memory**: Enable/disable conversation memory
    - **sessionId**: Optional session ID for memory (auto-generated if not provided)
    """
    return await ChatService.handleSearchAndAnswer(request, use_memory, currentUser)

@router.delete(
    "/session/{session_id}",
    status_code=status.HTTP_200_OK,
    description="Clear conversation memory for a specific session",
    response_model=SessionClearResponseDto
)
async def clear_session(
    session_id: str = Path(..., description="Session ID to clear"),
    currentUser: Dict = Depends(get_current_user)
):
    """Clear conversation memory for a specific session."""
    return ChatService.clear_session(session_id)

@router.get(
    "/session/{session_id}/history",
    status_code=status.HTTP_200_OK,
    description="Get conversation history for a session",
    response_model=ChatHistoryResponseDto
)
async def get_session_history(
    session_id: str = Path(..., description="Session ID to retrieve history for"),
    currentUser: Dict = Depends(get_current_user)
):
    """Get conversation history for a specific session."""
    return ChatService.get_session_history(session_id)

@router.get(
    "/sessions",
    status_code=status.HTTP_200_OK,
    description="Get all active sessions with metadata"
)
async def get_all_sessions(currentUser: Dict = Depends(get_current_user)):
    """Get all active sessions with message counts."""
    return ChatService.get_all_active_sessions(currentUser)

@router.post(
    "/session/{session_id}/clear",
    status_code=status.HTTP_200_OK,
    description="Alternative endpoint to clear session (POST method)",
    response_model=SessionClearResponseDto
)
async def clear_session_post(
    session_id: str = Path(..., description="Session ID to clear"),
    currentUser: Dict = Depends(get_current_user)
):
    """Alternative endpoint to clear session using POST method."""
    return ChatService.clear_session(session_id)

@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    description="Health check for chat service"
)
async def health_check(currentUser: Dict = Depends(get_current_user)):
    """Health check endpoint."""
    return ChatService.health_check()

@router.get(
    "/history",
     response_model=List[UserChatHistoryDto],
    status_code=status.HTTP_200_OK,
    description="Get all conversation histories")
async def get_all_histories(currentUser: Dict = Depends(get_current_user)):
    "Get all conversation histories"
    return await ChatService.getUserChatHistory(currentUser)
