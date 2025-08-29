"""API v1 controller for Projects."""
from typing import List

from fastapi import APIRouter, status

from app.core.models.pydantic.projects import CreateProjectRequestDto, ListProjectDto
from app.core.models.pydantic.category import CreateCategoryRequestDto, ListCategoryDto
from .project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description="Create a new project",
)
async def createProject(request: CreateProjectRequestDto):
    project = await ProjectService.create(request)
    return project


@router.get(
    "/",
    response_model=List[ListProjectDto],
    description="Get all projects",
)
async def listProjects():
    return await ProjectService.handleListAllProjects()


@router.post(
    "/{projectId}/category",
    status_code=status.HTTP_201_CREATED,
    description="Create a new category",
)
async def createProjectCategory(projectId: int, request: CreateCategoryRequestDto):
    category = await ProjectService.handleCreateProjectCategory(projectId, request)
    return category

@router.get(
    "/{projectId}/category",
    response_model=List[ListCategoryDto],
    description="Get all project categories",
)
async def listProjectCategories(projectId: int):
    return await ProjectService.handleListProjectCategoriesByProjectId(projectId)
