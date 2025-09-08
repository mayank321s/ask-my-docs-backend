"""API v1 controller for Chat."""
from fastapi import APIRouter, status, Form, Depends
from .chat_service import ChatService
from app.core.models.pydantic.chat import SearchAndAnswerRequestDto
from fastapi.responses import PlainTextResponse
from typing import Dict
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description="Search and answer",
)
async def searchAndAnswer(request: SearchAndAnswerRequestDto, current_user: Dict = Depends(get_current_user)):
    return await ChatService.handleSearchAndAnswer(request, current_user)


@router.post(
    "/ollama",
    status_code=status.HTTP_201_CREATED,
    description="Search and answer",
)
async def searchAndAnswerOllama(request: SearchAndAnswerRequestDto, current_user: Dict = Depends(get_current_user)):
    return await ChatService.handleSearchAndAnswerOllama(request, current_user)

@router.get("/health", status_code=status.HTTP_200_OK, response_class=PlainTextResponse)
async def chat_health(current_user: Dict = Depends(get_current_user)):
    return ChatService.health_check(current_user)