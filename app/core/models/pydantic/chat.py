from pydantic import BaseModel
from typing import Optional

class SearchAndAnswerRequestDto(BaseModel):
    query: str
    projectId: int
    categoryId: Optional[int] = None
