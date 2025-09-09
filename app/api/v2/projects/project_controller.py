"""API v1 controller for Projects."""
from typing import List, Dict

from fastapi import APIRouter, status, Depends

from app.core.models.pydantic.projects import CreateProjectRequestDto, ListProjectDto
from app.core.models.pydantic.category import CreateCategoryRequestDto, ListCategoryDto
from app.utils.jwt import get_current_user
from .project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description="Create a new project",
)
async def createProject(request: CreateProjectRequestDto, currentUser: Dict = Depends(get_current_user)):
    project = await ProjectService.create(request, currentUser)
    return project


@router.get(
    "/",
    response_model=List[ListProjectDto],
    description="Get all projects",
)
async def listProjects(currentUser: Dict = Depends(get_current_user)):
    return await ProjectService.handleListAllProjects(currentUser)


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
