import os
import zipfile
import requests
from typing import Optional, Tuple
from fastapi import HTTPException
from urllib.parse import urljoin
from app.core.pinecone.pinecone_client import processCodebaseFolder


class GitHubService:
    GITHUB_API_BASE = "https://api.github.com"
    ASSETS_DIR = os.path.abspath("tempAssets")

    @staticmethod
    def getHeaders() -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
        }
        if token := os.getenv("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @staticmethod
    def downloadRepository(owner: str, repo: str, ref: Optional[str] = None) -> Tuple[str, str]:
        try:
            if not os.path.exists(GitHubService.ASSETS_DIR):
                os.makedirs(GitHubService.ASSETS_DIR)

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

            zip_filename = f"{owner}_{repo}.zip"
            zip_path = os.path.join(GitHubService.ASSETS_DIR, zip_filename)
            extract_dir = os.path.join(GitHubService.ASSETS_DIR, f"{owner}_{repo}")

            with requests.get(downloadUrl, headers=GitHubService.getHeaders(), stream=True) as r:
                r.raise_for_status()
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if os.path.isdir(extract_dir):
                    import shutil
                    shutil.rmtree(extract_dir)

                zip_ref.extractall(extract_dir)

                
                extractedDirs = os.listdir(extract_dir)
                if extractedDirs:
                    extractedTopDir = os.path.join(extract_dir, extractedDirs[0])
                else:
                    extractedTopDir = extract_dir

                processCodebaseFolder(extractedTopDir,"nsc","technical-document")
                return zip_path, extractedTopDir

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
