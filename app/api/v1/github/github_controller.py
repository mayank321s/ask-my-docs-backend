from fastapi import APIRouter, Query
from typing import Optional
import os
from ..github.github_service import GitHubService

router = APIRouter(prefix="/github", tags=["github"])

@router.get("/download")
async def downloadGithubRepository(
    owner: str = Query(..., description="Repository owner/organization name"),
    repo: str = Query(..., description="Repository name"),
    projectId: int = Query(..., description="Project ID"),
    branchName: str = Query(..., description="Branch name"),
    categoryId: int = Query(..., description="Category ID"),
    ref: Optional[str] = Query(
        None,
        description="Branch, tag, or commit SHA"
    ),
):
    await GitHubService.downloadRepository(owner, repo, projectId, categoryId, branchName, ref)
    response = {
        "status": "success",
        "repository": f"{owner}/{repo}",
    }
    return response

