"""Service layer for Project operations (API v1)."""

from argparse import Namespace
from app.core.repository.project_repository import ProjectRepository
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.models.pydantic.projects import CreateProjectRequestDto, ListProjectDto
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from app.core.models.pydantic.category import CreateCategoryRequestDto, ListCategoryDto
from fastapi import HTTPException
from app.utils.common import convertStringToHyphen
from tortoise.transactions import in_transaction
from app.core.qdrant.qdrant_client import createCollection, createNamespace, deleteCollection

class ProjectService:
    """Provides CRUD operations for Projects for API v1."""

    @staticmethod
    async def create(request: CreateProjectRequestDto):
        try:
            existing = await ProjectRepository.findOneByClause({"name": request.name})
            if existing:
                raise HTTPException(status_code=409, detail="Project with this name already exists")

            async with in_transaction():
                projectDetail = await ProjectRepository.create(request.name)
                projectIndexName = convertStringToHyphen(request.name)
                
                createCollection(projectIndexName)
                await VectorIndexRepository.create({"indexName": projectIndexName, "projectId": projectDetail.id})

            return True
        except Exception as e:
            projectIndexName = convertStringToHyphen(request.name)
            if projectIndexName:
                deleteCollection(projectIndexName)
            raise HTTPException(status_code=500, detail=str(e))
        
    @staticmethod
    async def handleListAllProjects():
        """Return all projects with their associated vector index name."""
        try:
            projects_details = await ProjectRepository.list_all()
            result: list[ListProjectDto] = []
            for project in projects_details:
                indexDetails = await VectorIndexRepository.findOneByClause({"projectId": project.id})
                indexName = indexDetails.indexName if indexDetails else None

                result.append(
                    ListProjectDto(
                        id=project.id,
                        name=project.name,
                        indexName=indexName,
                        createdAt=project.createdAt,
                        updatedAt=project.updatedAt,
                    )
                )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def handleCreateProjectCategory(projectId: int, request: CreateCategoryRequestDto):
        try:     
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            existing = await VectorNamespaceRepository.findOneByClause({"categoryName": request.name, "indexId": projectIndexDetails.id})
            if existing:
                raise HTTPException(status_code=409, detail="Category with this name already exists")

            async with in_transaction():
                namespace = convertStringToHyphen(request.name)
                createNamespace(projectIndexDetails.indexName, namespace, projectDetail.name)
                await VectorNamespaceRepository.create({"name": namespace, "categoryName": request.name, "indexId": projectIndexDetails.id})

            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @staticmethod
    async def handleListProjectCategoriesByProjectId(projectId: int):
        try:     
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            vectorNamespaceDetails = await VectorNamespaceRepository.findAllByClause({"indexId": projectIndexDetails.id})
            result: list[ListCategoryDto] = []
            for namespace in vectorNamespaceDetails:
                result.append(
                    ListCategoryDto(
                        id=namespace.id,
                        name=namespace.name,
                        categoryName=namespace.categoryName,
                        createdAt=namespace.createdAt,
                        updatedAt=namespace.updatedAt,
                    )
                )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))