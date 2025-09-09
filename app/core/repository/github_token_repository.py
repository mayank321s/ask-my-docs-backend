from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import GithubToken


class GithubTokenRepository:

    @staticmethod
    async def create(createGithubTokenDto: Dict[str, Any]) -> GithubToken:
            logger.info("[v1] Creating GithubToken: {}", createGithubTokenDto)
            return await GithubToken.create(**createGithubTokenDto)

    @staticmethod
    async def list_all() -> List[GithubToken]:
        logger.info("[v1] Fetching all github tokens")
        return await GithubToken.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> GithubToken:
        logger.info("[v1] Fetching github token by id: {}", id)
        return await GithubToken.get_or_none(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> GithubToken:
        logger.info("[v1] Fetching github token by clause: {}", whereClause)
        return await GithubToken.get_or_none(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[GithubToken]:
        logger.info("[v1] Fetching github tokens by clause: {}", whereClause)
        return await GithubToken.filter(**whereClause).order_by("id")

    @staticmethod
    async def update(id: int, name: str) -> GithubToken:
        logger.info("[v1] Updating github token by id: {}", id)
        return await GithubToken.update(id=id, name=name)

    @staticmethod
    async def delete(id: int) -> GithubToken:
        logger.info("[v1] Deleting github token by id: {}", id)
        return await GithubToken.delete(id=id)
