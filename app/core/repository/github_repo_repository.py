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
        # Instead of get_or_none, use filter and fetch first matching record
        return await GithubRepo.filter(**whereClause).first()

    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[GithubRepo]:
        logger.info("[v1] Fetching github tokens by clause: {}", whereClause)
        return await GithubRepo.filter(**whereClause).order_by("id")

    @staticmethod
    async def updateByClause(whereClause: Dict[str, Any], **kwargs: Dict[str, Any]) -> GithubRepo:
        logger.info("[v1] Updating user by clause: {}", whereClause)
        # Get the object first
        githubRepo_obj = await GithubRepo.get_or_none(**whereClause)
        if not githubRepo_obj:
            return None
        
        # Update the object attributes
        for key, value in kwargs.items():
            setattr(githubRepo_obj, key, value)
        
        # Save the changes
        await githubRepo_obj.save()
        return githubRepo_obj


    @staticmethod
    async def delete(id: int) -> GithubRepo:
        logger.info("[v1] Deleting github token by id: {}", id)
        return await GithubRepo.delete(id=id)

    @staticmethod
    async def deleteBulkByIds(repo_ids: List[int]) -> int:
        logger.info("[v1] Bulk deleting documents by ids: {}", repo_ids)
        if not repo_ids:
            return 0
        return await GithubRepo.filter(id__in=repo_ids).delete()