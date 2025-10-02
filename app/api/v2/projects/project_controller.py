"""API v1 controller for Projects."""
from typing import List, Dict, Optional

from fastapi import APIRouter, status, Depends
from fastapi.params import Param, Query

from app.core.models.pydantic.projects import CreateProjectRequestDto, ListProjectDto, ListProjectsResponseDto
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
    response_model=ListProjectsResponseDto,
    description="Get all projects",
)
async def listProjects(currentUser: Dict = Depends(get_current_user),
    page: Optional[int] = Query(1, description="Page number for pagination"),
    limit: Optional[int] = Query(10, description="Number of items per page")):
    return await ProjectService.handleListAllProjects(currentUser, page, limit)


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

@router.delete(
    "/{projectId}",
    status_code=status.HTTP_200_OK,
    description="Delete a project",
)
async def deleteProject(projectId: int, currentUser: Dict = Depends(get_current_user)):
    return await ProjectService.handleDeleteProject(projectId, currentUser)
    

@router.delete(
    "/{projectId}/category/{categoryId}",
    status_code=status.HTTP_200_OK,
    description="Delete a project category",)
async def deleteProjectCategory(projectId: int, categoryId: int, currentUser: Dict = Depends(get_current_user)):
    return await ProjectService.handleDeleteProjectCategory(projectId, categoryId, currentUser)

@router.get("/{categoryId}/get-all-synced-data")
async def getAllSyncedRepos(
    categoryId: int,
    currentUser: Dict = Depends(get_current_user),
    projectId: Optional[int] = Query(None, description="Project ID"),
    repoName: Optional[str] = Query(None, description="Repository name"),
):
    result = await ProjectService.handleGetAllSyncedDataInCategory(currentUser, projectId, categoryId, repoName)
    response = {
        "status": "success",
        "data": result
    }
    return response
