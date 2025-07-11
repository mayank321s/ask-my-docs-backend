from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import VectorNamespace


class VectorNamespaceRepository:

    @staticmethod
    async def create(name: str) -> VectorNamespace:
        logger.info("[v1] Creating project: {}", name)
        return await VectorNamespace.create(name=name)

    @staticmethod
    async def list_all() -> List[VectorNamespace]:
        logger.info("[v1] Fetching all projects")
        return await VectorNamespace.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> VectorNamespace:
        logger.info("[v1] Fetching project by id: {}", id)
        return await VectorNamespace.get_or_none(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> VectorNamespace:
        logger.info("[v1] Fetching project by clause: {}", whereClause)
        return await VectorNamespace.get_or_none(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[VectorNamespace]:
        logger.info("[v1] Fetching projects by clause: {}", whereClause)
        return await VectorNamespace.filter(**whereClause).order_by("id")

    @staticmethod
    async def update(id: int, name: str) -> VectorNamespace:
        logger.info("[v1] Updating project by id: {}", id)
        return await VectorNamespace.update(id=id, name=name)

    @staticmethod
    async def delete(id: int) -> VectorNamespace:
        logger.info("[v1] Deleting project by id: {}", id)
        return await VectorNamespace.delete(id=id)
