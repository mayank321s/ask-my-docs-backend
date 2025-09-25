from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import GithubBranch


class GithubBranchRepository:

    @staticmethod
    async def create(createGithubBranchDto: Dict[str, Any]) -> GithubBranch:
            logger.info("[v1] Creating GithubBranch: {}", createGithubBranchDto)
            return await GithubBranch.create(**createGithubBranchDto)

    @staticmethod
    async def list_all() -> List[GithubBranch]:
        logger.info("[v1] Fetching all github tokens")
        return await GithubBranch.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> GithubBranch:
        logger.info("[v1] Fetching github token by id: {}", id)
        return await GithubBranch.get_or_none(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> GithubBranch:
        logger.info("[v1] Fetching github token by clause: {}", whereClause)
        return await GithubBranch.get_or_none(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[GithubBranch]:
        logger.info("[v1] Fetching github tokens by clause: {}", whereClause)
        return await GithubBranch.filter(**whereClause).order_by("id")

    @staticmethod
    async def updateByClause(whereClause: Dict[str, Any], **kwargs: Dict[str, Any]) -> GithubBranch:
        logger.info("[v1] Updating user by clause: {}", whereClause)
        # Get the object first
        githubBranch_obj = await GithubBranch.get_or_none(**whereClause)
        if not githubBranch_obj:
            return None
        
        # Update the object attributes
        for key, value in kwargs.items():
            setattr(githubBranch_obj, key, value)
        
        # Save the changes
        await githubBranch_obj.save()
        return githubBranch_obj


    @staticmethod
    async def delete(id: int) -> GithubBranch:
        logger.info("[v1] Deleting github token by id: {}", id)
        return await GithubBranch.delete(id=id)
