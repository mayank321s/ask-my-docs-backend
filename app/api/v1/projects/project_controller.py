"""API v1 controller for Projects."""
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.core.models.pydantic.projects import CreateProjectRequestDto, ListProjectDto, CreateProjectResponseDto
from .project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description="Create a new project",
)
async def create_project(request: CreateProjectRequestDto):
    project = await ProjectService.create(request)
    return project


@router.get(
    "/",
    response_model=List[ListProjectDto],
    description="Get all projects",
)
async def list_projects():
    projects = await ProjectService.list_all()
    return [ListProjectDto.model_validate(p) for p in projects]
