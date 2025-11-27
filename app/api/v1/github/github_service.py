import os
import zipfile
import requests
from typing import Optional
import shutil
from fastapi import HTTPException
from urllib.parse import urljoin
import requests
from urllib.parse import urljoin
import base64
from typing import Optional
from app.core.pinecone.pinecone_client import processCodebaseFolder
from app.core.repository.project_repository import ProjectRepository
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from app.core.pinecone.pinecone_client import upsertChunks
from app.core.chunker.chunker import chunkText

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
    async def downloadRepository(owner: str, repo: str, projectId: int, categoryId: int,branchName: str, ref: Optional[str] = None) -> bool:
        try:
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            vectorNamespaceDetails = await VectorNamespaceRepository.findOneByClause({"id": categoryId})
            if not vectorNamespaceDetails:
                raise HTTPException(status_code=404, detail="Category not found")

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
                url = f"repos/{owner}/{repo}/zipball/{branchName}"

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
                    shutil.rmtree(extract_dir)

                zip_ref.extractall(extract_dir)

                
                extractedDirs = os.listdir(extract_dir)
                if extractedDirs:
                    extractedTopDir = os.path.join(extract_dir, extractedDirs[0])
                else:
                    extractedTopDir = extract_dir


                processCodebaseFolder(extractedTopDir,projectIndexDetails.indexName,vectorNamespaceDetails.name, branchName)
            try:
                os.remove(zip_path)
            except OSError as e:
                print(f"Warning: Could not delete ZIP file {zip_path}: {e}")
            
            try:
                shutil.rmtree(extract_dir)
            except OSError as e:
                print(f"Warning: Could not delete extract directory {extract_dir}: {e}")
            return True

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

    @staticmethod
    async def fetchFileContentAtRef(owner: str, repo: str, filePath: str, ref: str) -> Optional[str]:
        """
        Fetch file content at a specific commit/ref
        """
        try:
            url = f"repos/{owner}/{repo}/contents/{filePath}"
            params = {"ref": ref}
            
            response = requests.get(
                urljoin(GitHubService.GITHUB_API_BASE, url),
                headers=GitHubService.getHeaders(),
                params=params
            )
            response.raise_for_status()
            
            fileData = response.json()
            
            # Decode base64 content
            if fileData.get("encoding") == "base64":
                content = base64.b64decode(fileData["content"]).decode('utf-8')
                return content
            else:
                return fileData.get("content", "")
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching file {filePath} at ref {ref}: {e}")
            return None

    @staticmethod
    async def fetchAndStorePrFiles(owner: str, repo: str, prNumber: int, projectId: int, categoryId: int) -> bool:
        """
        Fetch all files changed in a PR, chunk them, and store in Pinecone
        """
        try:
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            vectorNamespaceDetails = await VectorNamespaceRepository.findOneByClause({"id": categoryId})
            if not vectorNamespaceDetails:
                raise HTTPException(status_code=404, detail="Category not found")
            indexName = projectIndexDetails.indexName
            namespace = vectorNamespaceDetails.name
            filesUrl = f"repos/{owner}/{repo}/pulls/{prNumber}/files"
            filesResponse = requests.get(
                urljoin(GitHubService.GITHUB_API_BASE, filesUrl),
                headers=GitHubService.getHeaders()
            )
            filesResponse.raise_for_status()
            changedFiles = filesResponse.json()
            
            prUrl = f"repos/{owner}/{repo}/pulls/{prNumber}"
            prResponse = requests.get(
                urljoin(GitHubService.GITHUB_API_BASE, prUrl),
                headers=GitHubService.getHeaders()
            )
            prResponse.raise_for_status()
            prData = prResponse.json()
            
            baseSha = prData["base"]["sha"]
            headSha = prData["head"]["sha"]
            
            baseMetadata = {
                "repo": f"{owner or ''}/{repo or ''}",
                "pr_number": prNumber or 0,
                "pr_title": prData.get("title") or "",
                "pr_description": prData.get("body") or "",
                "pr_author": prData.get("user", {}).get("login") or "",
                "created_at": prData.get("created_at") or "",
                "merged_at": prData.get("merged_at") or "",
                "date": prData.get("merged_at") or ""
            }

            
            allChunks = []
            
            for file in changedFiles:
                filePath = file["filename"]
                fileStatus = file["status"]
                
                fileMetadata = {
                    **baseMetadata,
                    "file_path": filePath,
                    "file_status": fileStatus,
                    "additions": file["additions"],
                    "deletions": file["deletions"],
                    "changes": file["changes"]
                }
                
                if fileStatus != "added":
                    beforeContent = await GitHubService.fetchFileContentAtRef(owner, repo, filePath, baseSha)
                    if beforeContent:
                        beforeMetadata = {
                            **fileMetadata,
                            "version_type": "pr_before",
                            "commit_sha": baseSha
                        }
                        
                        beforeFileName = f"{filePath}_pr{prNumber}_before"
                        beforeChunks = chunkText(beforeContent, beforeMetadata, beforeFileName)
                        allChunks.extend(beforeChunks)
                
                if fileStatus != "removed":  # File exists after
                    afterContent = await GitHubService.fetchFileContentAtRef(owner, repo, filePath, headSha)
                    if afterContent:
                        afterMetadata = {
                            **fileMetadata,
                            "version_type": "pr_after",
                            "commit_sha": headSha
                        }
                        
                        afterFileName = f"{filePath}_pr{prNumber}_after"
                        afterChunks = chunkText(afterContent, afterMetadata, afterFileName)
                        allChunks.extend(afterChunks)
            
            if allChunks:
                upsertChunks(indexName, namespace, allChunks)
                print(f"Successfully stored {len(allChunks)} chunks for PR #{prNumber}")
                return True
            else:
                print(f"No chunks to store for PR #{prNumber}")
                return False
                
        except Exception as e:
            print(f"Error processing PR #{prNumber}: {e}")
            return False
        
    @staticmethod
    async def fetchAndStoreAllMergedPrs(owner: str, repo: str, projectId: int, categoryId: int) -> dict:
        """
        Fetch all merged PRs from a repository and store each one in the vector database
        """
        try:
            # Validate project and category exist
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            
            vectorNamespaceDetails = await VectorNamespaceRepository.findOneByClause({"id": categoryId})
            if not vectorNamespaceDetails:
                raise HTTPException(status_code=404, detail="Category not found")

            # Fetch all merged PRs with pagination
            all_merged_prs = []
            page = 1
            per_page = 100  # GitHub's max per page
            
            while True:
                prs_url = f"repos/{owner}/{repo}/pulls"
                params = {
                    "state": "closed",
                    "sort": "updated",
                    "direction": "asc",
                    "page": page,
                    "per_page": per_page 
                }
                
                response = requests.get(
                    urljoin(GitHubService.GITHUB_API_BASE, prs_url),
                    headers=GitHubService.getHeaders(),
                    params=params
                )
                response.raise_for_status()
                
                prs = response.json()
                
                # Filter for merged PRs only
                merged_prs = [pr for pr in prs if pr.get("merged_at") is not None]
                all_merged_prs.extend(merged_prs)
                
                # Break if we've reached the end or got less than requested
                if len(prs) < per_page:
                    break
                    
                page += 1

            print(f"Found {len(all_merged_prs)} merged PRs in {owner}/{repo}")

            # Process each merged PR
            successful_prs = []
            failed_prs = []
            
            for i, pr in enumerate(all_merged_prs, 1):
                pr_number = pr["number"]
                pr_title = pr.get("title", "")
                
                print(f"Processing PR #{pr_number} ({i}/{len(all_merged_prs)}): {pr_title}")
                
                try:
                    success = await GitHubService.fetchAndStorePrFiles(
                        owner=owner,
                        repo=repo,
                        prNumber=pr_number,
                        projectId=projectId,
                        categoryId=categoryId
                    )
                    
                    if success:
                        successful_prs.append({
                            "pr_number": pr_number,
                            "title": pr_title,
                            "merged_at": pr.get("merged_at")
                        })
                        print(f"✅ Successfully processed PR #{pr_number}")
                    else:
                        failed_prs.append({
                            "pr_number": pr_number,
                            "title": pr_title,
                            "error": "No chunks generated"
                        })
                        print(f"⚠️  PR #{pr_number} processed but no chunks generated")
                        
                except Exception as e:
                    failed_prs.append({
                        "pr_number": pr_number,
                        "title": pr_title,
                        "error": str(e)
                    })
                    print(f"❌ Failed to process PR #{pr_number}: {e}")
                    continue  # Continue with next PR even if one fails

            # Return summary
            result = {
                "total_merged_prs": len(all_merged_prs),
                "successful_prs": len(successful_prs),
                "failed_prs": len(failed_prs),
                "successful_pr_details": successful_prs,
                "failed_pr_details": failed_prs
            }
            
            print(f"\n📊 Processing Summary:")
            print(f"Total merged PRs found: {result['total_merged_prs']}")
            print(f"Successfully processed: {result['successful_prs']}")
            print(f"Failed to process: {result['failed_prs']}")
            
            return result

        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch PRs from repository: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing merged PRs: {str(e)}"
            )

