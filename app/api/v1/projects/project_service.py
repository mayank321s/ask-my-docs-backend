"""Service layer for Project operations (API v1)."""

from argparse import Namespace
from app.core.repository.project_repository import ProjectRepository
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.models.pydantic.projects import CreateProjectRequestDto
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from app.core.models.pydantic.category import CreateCategoryRequestDto
from fastapi import HTTPException
from app.utils.common import convertStringToHyphen
from tortoise.transactions import in_transaction
from app.core.pinecone.pinecone_client import createIndex, deleteIndex, createNamespace

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
                
                createIndex(projectIndexName)
                await VectorIndexRepository.create({"indexName": projectIndexName, "projectId": projectDetail.id})

            return True
        except Exception as e:
            deleteIndex(projectIndexName)
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def handleCreateProjectCategory(projectId: int, request: CreateCategoryRequestDto):
        try:
            existing = await VectorNamespaceRepository.findOneByClause({"categoryName": request.name, "projectId": projectId})
            if existing:
                raise HTTPException(status_code=409, detail="Category with this name already exists")
            
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})

            async with in_transaction():
                namespace = convertStringToHyphen(request.name)
                createNamespace(projectDetail.name, namespace, projectDetail.name)
                await VectorNamespaceRepository.create({"name": namespace, "categoryName":  request.name, "indexId": projectIndexDetails.id})

            return True
        except Exception as e:
            deleteIndex(categoryIndexName)
            raise HTTPException(status_code=500, detail=str(e))