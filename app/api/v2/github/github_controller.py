from fastapi import APIRouter, Query, Depends, BackgroundTasks
from typing import Optional, Dict
import os

from urllib3 import response
from ..github.github_service import GitHubService
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/github", tags=["github"])

@router.get("/download")
async def downloadGithubRepository(
    backgroundTasks: BackgroundTasks,
    repoUrl: str = Query(..., description="Repository URL"),
    projectId: int = Query(..., description="Project ID"),
    categoryId: int = Query(..., description="Category ID"),
    currentUser: Dict = Depends(get_current_user)
):
    await GitHubService.downloadRepository(repoUrl, projectId, categoryId, currentUser, backgroundTasks)
    response = {
        "status": "success",
        "repository": repoUrl,
        "message": "Code is being uploaded, please check back after few minutes."
    }
    return response

@router.get("/fetch-pr-files")
async def fetchPrFiles(
    backgroundTasks: BackgroundTasks,
    prUrl: str = Query(..., description="Pull request url"),
    projectId: int = Query(..., description="Project ID"),
    categoryId: int = Query(..., description="Category ID"),
    currentUser: Dict = Depends(get_current_user)
):
    await GitHubService.fetchAndStorePrFiles(prUrl, projectId, categoryId, currentUser, backgroundTasks)
    response = {
        "status": "success",
        "prUrl": prUrl,
        "message": "Code pull requests is being uploaded, please check back after few minutes"
    }
    return response

@router.get("/fetch-all-merged-pr")
async def fetchAllMergedPr(
    backgroundTasks: BackgroundTasks,
    repoUrl: str = Query(..., description="Repository url"),
    projectId: int = Query(..., description="Project ID"),
    categoryId: int = Query(..., description="Category ID"),
    currentUser: Dict = Depends(get_current_user)
):
    await GitHubService.fetchAndStoreAllMergedPrs(repoUrl, projectId, categoryId, currentUser, backgroundTasks)
    response ={
        "status": "success",
        "repoUrl": f"{repoUrl}",
        "message": "All merged pull requests are being uploaded, please check back after few minutes"
    }
    return response

@router.post("/store-github-token")
async def storeGithubToken(
    githubToken: str = Query(..., description="GitHub Token"),
    currentUser: Dict = Depends(get_current_user)
):
    await GitHubService.handleStoreGithubToken(githubToken, currentUser)
    response ={
        "status": "success",
    }
    return response

@router.get("/get-github-token")
async def getGithubToken(
    currentUser: Dict = Depends(get_current_user)
):
    token = await GitHubService.handleGetGithubToken(currentUser)
    response ={
        "status": "success",
        "github_token": token
    }
    return response

@router.get("/get-all-repositories")
async def getAllRepositories(
    currentUser: Dict = Depends(get_current_user)
):
    repositories = await GitHubService.handleGetAllRepositories(currentUser)
    response = {
        "status": "success",
        "repositories": repositories
    }
    return response

@router.get("/get-all-synced-repositories")
async def getAllSyncedRepos(
    currentUser: Dict = Depends(get_current_user),
    projectId: Optional[int] = Query(None, description="Project ID"),
    categoryId: Optional[int] = Query(None, description="Category ID"),
    repoName: Optional[str] = Query(None, description="Repository name"),
):
    repos = await GitHubService.handleGetAllSyncedRepos(currentUser, projectId, categoryId, repoName)
    response = {
        "status": "success",
        "synced_repositories": repos
    }
    return response
