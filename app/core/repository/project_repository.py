from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import Project


class ProjectRepository:

    @staticmethod
    async def create(name: str) -> Project:
        logger.info("[v1] Creating project: {}", name)
        return await Project.create(name=name)

    @staticmethod
    async def list_all() -> List[Project]:
        logger.info("[v1] Fetching all projects")
        return await Project.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> Project:
        logger.info("[v1] Fetching project by id: {}", id)
        return await Project.get_or_none(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> Project:
        logger.info("[v1] Fetching project by clause: {}", whereClause)
        return await Project.get_or_none(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[Project]:
        logger.info("[v1] Fetching projects by clause: {}", whereClause)
        return await Project.filter(**whereClause).order_by("id")

    @staticmethod
    async def update(id: int, name: str) -> Project:
        logger.info("[v1] Updating project by id: {}", id)
        return await Project.update(id=id, name=name)

    @staticmethod
    async def delete(id: int) -> Project:
        logger.info("[v1] Deleting project by id: {}", id)
        return await Project.delete(id=id)
