"""Pydantic schemas for Category model."""

from pydantic import BaseModel, Field


class CreateCategoryRequestDto(BaseModel):
    name: str = Field(..., max_length=255)