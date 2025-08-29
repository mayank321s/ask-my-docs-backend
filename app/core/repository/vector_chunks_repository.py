from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import VectorChunk


class VectorChunkRepository:

    @staticmethod
    async def create(createVectorChunkDto: Dict[str, Any]) -> VectorChunk:
        logger.info("[v1] Creating vector chunk: {}", createVectorChunkDto)
        return await VectorChunk.create(**createVectorChunkDto)

    @staticmethod
    async def list_all() -> List[VectorChunk]:
        logger.info("[v1] Fetching all vector chunks")
        return await VectorChunk.all().order_by("id")
    
    @staticmethod
    async def get_by_id(id: int) -> VectorChunk:
        logger.info("[v1] Fetching vector chunk by id: {}", id)
        return await VectorChunk.get(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> VectorChunk:
        logger.info("[v1] Fetching vector chunk by clause: {}", whereClause)
        return await VectorChunk.get(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[VectorChunk]:
        logger.info("[v1] Fetching vector chunks by clause: {}", whereClause)
        return await VectorChunk.filter(**whereClause).order_by("id")

    @staticmethod
    async def deleteByClause(whereClause: Dict[str, Any]) -> VectorChunk:
        logger.info("[v1] Deleting vector chunk by clause: {}", whereClause)
        return await VectorChunk.delete(**whereClause)
