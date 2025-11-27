"""Pydantic schemas for Category model."""
from pydantic import BaseModel, Field

class LoginRequestDto(BaseModel):
    emailAddress: str = Field(..., max_length=255)
    password: str = Field(..., max_length=255)
    

class RegisterRequestDto(BaseModel):
    firstName: str = Field(..., max_length=255)
    lastName: str = Field(..., max_length=255)
    emailAddress: str = Field(..., max_length=255)
    password: str = Field(..., max_length=255)
    
class jwtDto(BaseModel):
    userId: int
    emailAddress: str
    roleCode: str