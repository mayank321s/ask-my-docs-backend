from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import GithubRepo


class GithubRepoRepository:

    @staticmethod
    async def create(createGithubRepoDto: Dict[str, Any]) -> GithubRepo:
            logger.info("[v1] Creating GithubRepo: {}", createGithubRepoDto)
            return await GithubRepo.create(**createGithubRepoDto)

    @staticmethod
    async def list_all() -> List[GithubRepo]:
        logger.info("[v1] Fetching all github tokens")
        return await GithubRepo.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> GithubRepo:
        logger.info("[v1] Fetching github token by id: {}", id)
        return await GithubRepo.get_or_none(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> GithubRepo:
        logger.info("[v1] Fetching github token by clause: {}", whereClause)
        return await GithubRepo.get_or_none(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[GithubRepo]:
        logger.info("[v1] Fetching github tokens by clause: {}", whereClause)
        return await GithubRepo.filter(**whereClause).order_by("id")

    @staticmethod
    async def update(id: int, name: str) -> GithubRepo:
        logger.info("[v1] Updating github token by id: {}", id)
        return await GithubRepo.update(id=id, name=name)

    @staticmethod
    async def delete(id: int) -> GithubRepo:
        logger.info("[v1] Deleting github token by id: {}", id)
        return await GithubRepo.delete(id=id)
