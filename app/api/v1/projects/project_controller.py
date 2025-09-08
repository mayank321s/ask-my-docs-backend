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
async def createProject(request: CreateProjectRequestDto, current_user: Dict = Depends(get_current_user)):
    project = await ProjectService.create(request, current_user)
    return project



@router.get(
    "/",
    response_model=List[ListProjectDto],
    description="Get all projects",
)
async def listProjects(current_user: Dict = Depends(get_current_user)):
    return await ProjectService.handleListAllProjects(current_user)



@router.post(
    "/{projectId}/category",
    status_code=status.HTTP_201_CREATED,
    description="Create a new category",
)
async def createProjectCategory(projectId: int, request: CreateCategoryRequestDto, current_user: Dict = Depends(get_current_user)):
    category = await ProjectService.handleCreateProjectCategory(projectId, request, current_user)
    return category

@router.get(
    "/{projectId}/category",
    response_model=List[ListCategoryDto],
    description="Get all project categories",
)
async def listProjectCategories(projectId: int, current_user: Dict = Depends(get_current_user)):
    return await ProjectService.handleListProjectCategoriesByProjectId(projectId, current_user)
