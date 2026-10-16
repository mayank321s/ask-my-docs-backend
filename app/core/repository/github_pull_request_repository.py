from typing import List, Dict, Any
from loguru import logger

from app.core.models.tortoise import GithubPullRequest


class GithubPullRequestRepository:

    @staticmethod
    async def create(createGithubPullRequestDto: Dict[str, Any]) -> GithubPullRequest:
            logger.info("[v1] Creating GithubPullRequest: {}", createGithubPullRequestDto)
            return await GithubPullRequest.create(**createGithubPullRequestDto)

    @staticmethod
    async def list_all() -> List[GithubPullRequest]:
        logger.info("[v1] Fetching all github tokens")
        return await GithubPullRequest.all().order_by("id")

    @staticmethod
    async def get_by_id(id: int) -> GithubPullRequest:
        logger.info("[v1] Fetching github token by id: {}", id)
        return await GithubPullRequest.get_or_none(id=id)

    @staticmethod
    async def findOneByClause(whereClause: Dict[str, Any]) -> GithubPullRequest:
        logger.info("[v1] Fetching github token by clause: {}", whereClause)
        return await GithubPullRequest.get_or_none(**whereClause)
    
    @staticmethod
    async def findAllByClause(whereClause: Dict[str, Any]) -> List[GithubPullRequest]:
        logger.info("[v1] Fetching github tokens by clause: {}", whereClause)
        return await GithubPullRequest.filter(**whereClause).order_by("id")

    @staticmethod
    async def updateByClause(whereClause: Dict[str, Any], **kwargs: Dict[str, Any]) -> GithubPullRequest:
        logger.info("[v1] Updating user by clause: {}", whereClause)
        # Get the object first
        githubPullRequest_obj = await GithubPullRequest.get_or_none(**whereClause)
        if not githubPullRequest_obj:
            return None
        
        # Update the object attributes
        for key, value in kwargs.items():
            setattr(githubPullRequest_obj, key, value)
        
        # Save the changes
        await githubPullRequest_obj.save()
        return githubPullRequest_obj


    @staticmethod
    async def delete(id: int) -> GithubPullRequest:
        logger.info("[v1] Deleting github token by id: {}", id)
        return await GithubPullRequest.delete(id=id)

    @staticmethod
    async def deleteBulkByIds(pr_ids: List[int]) -> int:
        logger.info("[v1] Bulk deleting documents by ids: {}", pr_ids)
        if not pr_ids:
            return 0
        return await GithubPullRequest.filter(id__in=pr_ids).delete()
