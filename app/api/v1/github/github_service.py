import os
import tempfile
import zipfile
import requests
from typing import Optional, Tuple
from fastapi import HTTPException
from urllib.parse import urljoin

class GitHubService:
    GITHUB_API_BASE = "https://api.github.com"
    
    @staticmethod
    def getHeaders() -> dict:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github+json",
        }
        # Add GitHub token if available for higher rate limits, facing limit error
        if token := os.getenv("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    @staticmethod
    def downloadRepository(owner: str, repo: str, ref: Optional[str] = None) -> Tuple[str, str]:
        try:
            if ref:
                url = f"repos/{owner}/{repo}/zipball/{ref}"
            else:
                repoInfoUrl = f"repos/{owner}/{repo}"
                response = requests.get(
                    urljoin(GitHubService.GITHUB_API_BASE, repoInfoUrl),
                    headers=GitHubService.getHeaders()
                )
                response.raise_for_status()
                defaultBranch = response.json().get("default_branch", "main")
                url = f"repos/{owner}/{repo}/zipball/{defaultBranch}"
            
            downloadUrl = urljoin(GitHubService.GITHUB_API_BASE, url)
            
            with tempfile.TemporaryDirectory() as tempDir:
                zipPath = os.path.join(tempDir, "repo.zip")
                
                with requests.get(downloadUrl, headers=GitHubService.getHeaders(), stream=True) as r:
                    r.raise_for_status()
                    with open(zipPath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                
                extractDir = tempfile.mkdtemp()
                with zipfile.ZipFile(zipPath, 'r') as zip_ref:
                    zip_ref.extractall(extractDir)
                    extractedDir = os.listdir(extractDir)[0]
                    extractedPath = os.path.join(extractDir, extractedDir)
                    
                    return extractedDir, extractedPath
                    
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download repository: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing the repository: {str(e)}"
            )
