"""API v1 controller for Projects."""
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.core.models.pydantic.projects import ProjectCreate, ProjectRead
from .project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    description="Create a new project",
)
async def create_project(dto: ProjectCreate):
    project = await ProjectService.create(dto)
    return ProjectRead.model_validate(project)


@router.get(
    "/",
    response_model=List[ProjectRead],
    description="Get all projects",
)
async def list_projects():
    projects = await ProjectService.list_all()
    return [ProjectRead.model_validate(p) for p in projects]
