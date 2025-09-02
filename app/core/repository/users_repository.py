from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import Users  


class UsersRepository:

    @staticmethod
    async def create(createUsersDto: Dict[str, Any]) -> Users:
        logger.info("[v1] Creating user: {}", createUsersDto)
        return await Users.create(**createUsersDto)

    @staticmethod
    async def list_all() -> List[Users]:
        logger.info("[v1] Fetching all users")
        return await Users.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> Users:
        logger.info("[v1] Fetching user by id: {}", id)
        return await Users.get(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> Users:
        logger.info("[v1] Fetching user by clause: {}", whereClause)
        return await Users.get(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[Users]:
        logger.info("[v1] Fetching users by clause: {}", whereClause)
        return await Users.filter(**whereClause).order_by("id")

    @staticmethod
    async def updateByClause(whereClause: Dict[str, Any], **kwargs: Dict[str, Any]) -> Users:
        logger.info("[v1] Updating user by clause: {}", whereClause)
        return await Users.update(**whereClause, **kwargs)

    @staticmethod
    async def deleteByClause(whereClause: Dict[str, Any]) -> int:
        logger.info("[v1] Deleting user by clause: {}", whereClause)
        return await Users.delete(**whereClause)
