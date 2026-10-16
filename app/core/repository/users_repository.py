from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import User  


class UserRepository:

    @staticmethod
    async def create(createUsersDto: Dict[str, Any]) -> User:
        logger.info("[v1] Creating user: {}", createUsersDto)
        return await User.create(**createUsersDto)

    @staticmethod
    async def list_all() -> List[User]:
        logger.info("[v1] Fetching all users")
        return await User.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> User:
        logger.info("[v1] Fetching user by id: {}", id)
        return await User.get_or_none(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> User:
        logger.info("[v1] Fetching user by clause: {}", whereClause)
        return await User.get_or_none(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[User]:
        logger.info("[v1] Fetching users by clause: {}", whereClause)
        return await User.filter(**whereClause).order_by("id")

    @staticmethod
    async def updateByClause(whereClause: Dict[str, Any], **kwargs: Dict[str, Any]) -> User:
        logger.info("[v1] Updating user by clause: {}", whereClause)
        return await User.update(**whereClause, **kwargs)

    @staticmethod
    async def deleteByClause(whereClause: Dict[str, Any]) -> int:
        logger.info("[v1] Deleting user by clause: {}", whereClause)
        return await User.delete(**whereClause)
