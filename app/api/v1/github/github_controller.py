from fastapi import APIRouter, Query
from typing import Optional
import os
from ..github.github_service import GitHubService

router = APIRouter(prefix="/github", tags=["github"])

@router.get("/download")
async def downloadGithubRepository(
    owner: str = Query(..., description="Repository owner/organization name"),
    repo: str = Query(..., description="Repository name"),
    ref: Optional[str] = Query(
        None,
        description="Branch, tag, or commit SHA"
    ),
):
    extractedDirectory, extractedPath = GitHubService.downloadRepository(owner, repo, ref)
    totalSize = 0
    fileCount = 0
    for dirpath, _, filenames in os.walk(extractedDirectory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            totalSize += os.path.getsize(fp)
            fileCount += 1
    response = {
        "status": "success",
        "repository": f"{owner}/{repo}",
        "ref": ref, 
        "extracted_directory": extractedDirectory,
        "extracted_path": extractedPath,
        "file_count": fileCount,
        "total_size_mb": round(totalSize / (1024 * 1024), 2)
    }
    return response

