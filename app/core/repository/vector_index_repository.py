from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import VectorIndex


class VectorIndexRepository:

    @staticmethod
    async def create(createVectorIndexDto: Dict[str, Any]) -> VectorIndex:
        logger.info("[v1] Creating vector index: {}", createVectorIndexDto)
        return await VectorIndex.create(**createVectorIndexDto)

    @staticmethod
    async def list_all() -> List[VectorIndex]:
        logger.info("[v1] Fetching all vector indexes")
        return await VectorIndex.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> VectorIndex:
        logger.info("[v1] Fetching vector index by id: {}", id)
        return await VectorIndex.get(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> VectorIndex:
        logger.info("[v1] Fetching vector index by clause: {}", whereClause)
        return await VectorIndex.get(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[VectorIndex]:
        logger.info("[v1] Fetching vector indexes by clause: {}", whereClause)
        return await VectorIndex.filter(**whereClause).order_by("id")

    @staticmethod
    async def updateByClause(whereClause: Dict[str, Any], name: str) -> VectorIndex:
        logger.info("[v1] Updating vector index by clause: {}", whereClause)
        return await VectorIndex.update(**whereClause, name=name)

    @staticmethod
    async def deleteByClause(whereClause: Dict[str, Any]) -> VectorIndex:
        logger.info("[v1] Deleting vector index by clause: {}", whereClause)
        return await VectorIndex.delete(**whereClause)
