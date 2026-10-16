from pydantic import BaseModel
from typing import Optional

from app.core.models.pydantic.pagination import PaginationResponseDto

class SearchAndAnswerRequestDto(BaseModel):
    projectId: Optional[int] = None
    query: str
    categoryId: Optional[int] = None
    sessionId: Optional[str] = None 

class ChatHistoryResponseDto(BaseModel):
    sessionId: str
    history: list

class SessionClearResponseDto(BaseModel):
    sessionId: str
    message: str
    success: bool

class UserChatHistoryDto(BaseModel):
    ProjectId: int
    categoryId: Optional[int] = None
    sessionId: Optional[str] = None
    chatTitle: Optional[str] = None
    chatHistory: list    
    
class UserChatHistoryResponseDto(BaseModel):
    data: list[UserChatHistoryDto]
    pagination: PaginationResponseDto  