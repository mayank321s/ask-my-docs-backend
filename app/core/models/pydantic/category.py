"""Pydantic schemas for Category model."""
from pydantic import BaseModel, Field
from datetime import datetime

class CreateCategoryRequestDto(BaseModel):
    name: str = Field(..., max_length=255)
    
    
class ListCategoryDto(BaseModel):
    id: int
    name: str
    categoryName: str
    createdAt: datetime
    updatedAt: datetime