"""Service layer for Project operations (API v1)."""

from sre_parse import SUCCESS
from app.core.repository.project_repository import ProjectRepository
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.models.pydantic.projects import CreateProjectRequestDto, ListProjectDto, CreateProjectResponseDto
from fastapi import HTTPException
from app.utils.common import convertStringToHyphen
from tortoise.transactions import in_transaction
from app.core.pinecone.pinecone_client import createIndex, deleteIndex

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
