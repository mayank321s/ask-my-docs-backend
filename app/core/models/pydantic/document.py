from datetime import datetime
from pydantic import BaseModel, Field

class ListDocumentDto(BaseModel):
    """Schema for reading / returning a document."""

    id: int
    name: str
    createdAt: datetime
    updatedAt: datetime