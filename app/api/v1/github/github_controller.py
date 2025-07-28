from fastapi import APIRouter, Query
from typing import Optional
import os

from urllib3 import response
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

@router.get("/fetch-pr-files")
async def fetchPrFiles(
    owner: str = Query(..., description="Repository owner/organization name"),
    repo: str = Query(..., description="Repository name"),
    prNumber: int = Query(..., description="Pull request number"),
    projectId: int = Query(..., description="Project ID"),
    categoryId: int = Query(..., description="Category ID"),
):
    await GitHubService.fetchAndStorePrFiles(owner, repo, prNumber, projectId, categoryId)
    response = {
        "status": "success",
        "repository": f"{owner}/{repo}",
        "pr_number": prNumber,
    }
    return response

@router.get("/fetch-all-merged-pr")
async def fetchAllMergedPr(
    owner: str = Query(..., description="Repository owner/organization name"),
    repo: str = Query(..., description="Repository name"),
    projectId: int = Query(..., description="Project ID"),
    categoryId: int = Query(..., description="Category ID"),
):
    await GitHubService.fetchAndStoreAllMergedPrs(owner, repo, projectId, categoryId)
    response ={
        "status": "success",
        "repository": f"{owner}/{repo}",
    }
    return response

