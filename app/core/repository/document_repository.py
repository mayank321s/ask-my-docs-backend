from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import Document


class DocumentRepository:

    @staticmethod
    async def create(createDocumentDto: Dict[str, Any]) -> Document:
        logger.info("[v1] Creating document: {}", createDocumentDto)
        return await Document.create(**createDocumentDto)

    @staticmethod
    async def list_all() -> List[Document]:
        logger.info("[v1] Fetching all documents")
        return await Document.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> Document:
        logger.info("[v1] Fetching document by id: {}", id)
        return await Document.get(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> Document:
        logger.info("[v1] Fetching document by clause: {}", whereClause)
        return await Document.get(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[Document]:
        logger.info("[v1] Fetching documents by clause: {}", whereClause)
        return await Document.filter(**whereClause).order_by("id")

    @staticmethod
    async def deleteByClause(whereClause: Dict[str, Any]) -> Document:
        logger.info("[v1] Deleting document by clause: {}", whereClause)
        return await Document.delete(**whereClause)
