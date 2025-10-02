from typing import List, Dict, Any, Tuple
from loguru import logger

from app.core.models.tortoise import Project


class ProjectRepository:

    @staticmethod
    async def create(createProjectDto: Dict[str, Any]) -> Project:
            logger.info("[v1] Creating Project: {}", createProjectDto)
            return await Project.create(**createProjectDto)

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
    async def findAllByClause(
        whereClause: Dict[str, Any],
        offset: int = 0,
        limit: int = 10
    ) -> Tuple[List[Project], int]:
        """
        Fetch projects by clause with pagination support.
        Returns tuple of (projects_list, total_count)
        """
        logger.info("[v1] Fetching projects by clause: {}", whereClause)
        
        # Get total count before applying pagination
        totalCount = await Project.filter(**whereClause).count()
        
        # Fetch paginated results ordered by createdAt descending (latest first)
        projects = await Project.filter(**whereClause)\
            .order_by("-createdAt")\
            .offset(offset)\
            .limit(limit)
        
        return projects, totalCount

    @staticmethod
    async def update(id: int, name: str) -> Project:
        logger.info("[v1] Updating project by id: {}", id)
        return await Project.update(id=id, name=name)

    @staticmethod
    async def deleteByClause(whereClause: Dict[str, Any]) -> int:
        logger.info("[v1] Deleting project by clause: {}", whereClause)
        # Use filter().delete() instead of Model.delete(**kwargs)
        return await Project.filter(**whereClause).delete()
