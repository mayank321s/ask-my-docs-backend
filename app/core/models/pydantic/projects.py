"""Pydantic schemas for Project model."""
from datetime import datetime
from pydantic import BaseModel, Field


class CreateProjectRequestDto(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., max_length=255)
    


class CreateProjectResponseDto(BaseModel):
    """Schema for creating a new project."""
    success: bool


class ListProjectDto(BaseModel):
    """Schema for reading / returning a project."""

    id: int
    name: str
    indexName: str
    createdAt: datetime
    updatedAt: datetime

    class Config:
        orm_mode = True

