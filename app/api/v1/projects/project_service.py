"""Service layer for Project operations (API v1)."""

from app.core.repository.project_repository import ProjectRepository
from app.core.models.pydantic.projects import ProjectCreate, ProjectRead
from fastapi import HTTPException

class ProjectService:
    """Provides CRUD operations for Projects for API v1."""

    @staticmethod
    async def create(dto: ProjectCreate):
        existing = await ProjectRepository.list_all()
        if any(p.name.lower() == dto.name.lower() for p in existing):
            raise HTTPException(status_code=409, detail="Project with this name already exists")

        project = await ProjectRepository.create(dto.name)
        return ProjectRead.model_validate(project)
