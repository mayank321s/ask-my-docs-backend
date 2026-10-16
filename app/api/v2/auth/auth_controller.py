"""API v1 controller for Chat."""
from fastapi import APIRouter, status, Form
from .auth_service import AuthService
from app.core.models.pydantic.auth import LoginRequestDto, RegisterRequestDto

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/login",
    status_code=status.HTTP_201_CREATED,
    description="Login",
)
async def login(request: LoginRequestDto):
    return await AuthService.handleLogin(request)

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    description="Register",
)
async def register(request: RegisterRequestDto):
    return await AuthService.handleRegister(request)
