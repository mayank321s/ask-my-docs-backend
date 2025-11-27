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
    async def deleteByClause(whereClause: Dict[str, Any]) -> int:
        logger.info("[v1] Deleting Document by clause: {}", whereClause)
        # Use filter().delete() instead of Model.delete(**kwargs)
        return await Document.filter(**whereClause).delete()
    
    @staticmethod
    async def deleteBulkByIds(document_ids: List[int]) -> int:
        logger.info("[v1] Bulk deleting documents by ids: {}", document_ids)
        if not document_ids:
            return 0
        return await Document.filter(id__in=document_ids).delete()
