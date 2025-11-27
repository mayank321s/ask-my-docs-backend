from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import VectorNamespace


class VectorNamespaceRepository:

    @staticmethod
    async def create(VectorNamespaceData: Dict[str, Any]) -> VectorNamespace:
        logger.info("[v1] Creating vector namespace: {}", VectorNamespaceData)
        return await VectorNamespace.create(**VectorNamespaceData)

    @staticmethod
    async def list_all() -> List[VectorNamespace]:
        logger.info("[v1] Fetching all vector namespaces")
        return await VectorNamespace.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> VectorNamespace:
        logger.info("[v1] Fetching vector namespace by id: {}", id)
        return await VectorNamespace.get_or_none(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> VectorNamespace:
        logger.info("[v1] Fetching vector namespace by clause: {}", whereClause)
        return await VectorNamespace.get_or_none(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[VectorNamespace]:
        logger.info("[v1] Fetching vector namespaces by clause: {}", whereClause)
        return await VectorNamespace.filter(**whereClause).order_by("id")

    @staticmethod
    async def update(id: int, name: str) -> VectorNamespace:
        logger.info("[v1] Updating vector namespace by id: {}", id)
        return await VectorNamespace.update(id=id, name=name)

    @staticmethod
    async def deleteByClause(whereClause: Dict[str, Any]) -> int:
        logger.info("[v1] Deleting vector namespace by clause: {}", whereClause)
        return await VectorNamespace.filter(**whereClause).delete()

    @staticmethod
    async def deleteBulkByIds(category_ids: List[int]) -> int:
        logger.info("[v1] Bulk deleting namespaces by ids: {}", category_ids)
        if not category_ids:
            return 0
        return await VectorNamespace.filter(id__in=category_ids).delete()