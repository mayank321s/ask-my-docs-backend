"""API v1 controller for Chat."""
from fastapi import APIRouter, status, Form
from .chat_service import ChatService
from app.core.models.pydantic.chat import SearchAndAnswerRequestDto

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description="Search and answer",
)
async def searchAndAnswer(request: SearchAndAnswerRequestDto):
    return await ChatService.handleSearchAndAnswer(request)


@router.post(
    "/ollama",
    status_code=status.HTTP_201_CREATED,
    description="Search and answer",
)
async def searchAndAnswerOllama(request: SearchAndAnswerRequestDto):
    return await ChatService.handleSearchAndAnswerOllama(request)