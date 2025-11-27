from typing import List, Dict, Any, Tuple
from loguru import logger

from app.core.models.tortoise import Chat  


class ChatRepository:

    @staticmethod
    async def create(createChatsDto: Dict[str, Any]) -> Chat:
        logger.info("[v1] Creating user: {}", createChatsDto)
        return await Chat.create(**createChatsDto)

    @staticmethod
    async def list_all() -> List[Chat]:
        logger.info("[v1] Fetching all users")
        return await Chat.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> Chat:
        logger.info("[v1] Fetching user by id: {}", id)
        return await Chat.get_or_none(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> Chat:
        logger.info("[v1] Fetching user by clause: {}", whereClause)
        return await Chat.get_or_none(**whereClause)
    
    @staticmethod
    async def findAllByClause(
        whereClause: Dict[str, Any],
        offset: int = 0,
        limit: int = 10
    ) -> Tuple[List[Chat], int]:
        """
        Fetch chats by clause with pagination support.
        Returns tuple of (chats_list, total_count)
        """
        logger.info("[v1] Fetching chats by clause: {}", whereClause)
        
        # Get total count before applying pagination
        totalCount = await Chat.filter(**whereClause).count()
        
        # Fetch paginated results ordered by createdAt descending (latest first)
        chats = await Chat.filter(**whereClause)\
            .order_by("-updatedAt")\
            .offset(offset)\
            .limit(limit)
        
        return chats, totalCount

    @staticmethod
    async def updateByClause(whereClause: Dict[str, Any], **kwargs: Dict[str, Any]) -> Chat:
        logger.info("[v1] Updating user by clause: {}", whereClause)
        # Get the object first
        chat_obj = await Chat.get_or_none(**whereClause)
        if not chat_obj:
            return None
        
        # Update the object attributes
        for key, value in kwargs.items():
            setattr(chat_obj, key, value)
        
        # Save the changes
        await chat_obj.save()
        return chat_obj


    @staticmethod
    async def deleteByClause(whereClause: Dict[str, Any]) -> int:
        logger.info("[v1] Deleting user by clause: {}", whereClause)
        return await Chat.delete(**whereClause)
