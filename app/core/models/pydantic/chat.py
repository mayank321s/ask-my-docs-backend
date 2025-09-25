from pydantic import BaseModel
from typing import Optional

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
    chatHistory: list    