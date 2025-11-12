import os
import zipfile
import requests
from typing import Optional , Dict, List
import shutil
from fastapi import HTTPException
from urllib.parse import urljoin
import requests
import base64
from app.core.repository.project_repository import ProjectRepository
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from app.core.repository.github_token_repository import GithubTokenRepository
from app.core.repository.github_branch_repository import GithubBranchRepository
from app.core.repository.github_repo_repository import GithubRepoRepository
from app.core.repository.github_pull_request_repository import GithubPullRequestRepository
from app.core.qdrant.qdrant_client import ( upsertChunksOllama, processCodebaseFolder )
from app.core.chunker.chunker import chunkText
import re
import httpx
from fastapi import BackgroundTasks
import asyncio
from starlette.concurrency import run_in_threadpool
from functools import partial

class GitHubService:
    GITHUB_API_BASE = "https://api.github.com"
    ASSETS_DIR = os.path.abspath("tempAssets")
    tokenDetails = None

    @staticmethod
    async def getHeaders(userId) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
        }
        tokenDetails =  GitHubService.tokenDetails 
        if tokenDetails is None:
            tokenDetails = await GithubTokenRepository.findOneByClause({"userId": userId})
        if tokenDetails and tokenDetails.token:
            headers["Authorization"] = f"Bearer {tokenDetails.token}"
            GitHubService.tokenDetails = tokenDetails
        else:
            headers["Authorization"] = "Bearer " + os.getenv("GITHUB_TOKEN")
        return headers




    @staticmethod
    async def process_downloaded_repo(zip_path: str, extract_dir: str, index_name: str,
                                    namespace_name: str, branch: str, repo_id: int,
                                    user_id: str, download_url: str):
        """Keep as async def - runs in main event loop, can access DB connections"""
        try:
            loop = asyncio.get_running_loop()
            
            # Run blocking file operations in thread pool
            await loop.run_in_executor(
                None,  # Uses default ThreadPoolExecutor
                GitHubService._extract_and_process_files,
                zip_path, extract_dir, index_name, namespace_name, branch
            )

            # NOW async DB operations work fine - same event loop!
            await GithubRepoRepository.updateByClause({"id": repo_id}, status="active")
            branchDetails = await GithubBranchRepository.findOneByClause({
                "githubRepoId": repo_id,
                "branchName": branch
            })
            if branchDetails:
                await GithubBranchRepository.updateByClause({"id": branchDetails.id}, status="active")

            # Cleanup files in thread pool
            await loop.run_in_executor(
                None,
                GitHubService._cleanup_files,
                zip_path, extract_dir
            )
            
        except Exception as e:
            await GithubRepoRepository.updateByClause({"id": repo_id}, status="failed")
            print(f"Error processing downloaded repo: {e}")

    @staticmethod
    def _extract_and_process_files(zip_path: str, extract_dir: str, 
                                index_name: str, namespace_name: str, branch: str):
        """Synchronous helper - contains ALL blocking file operations"""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if os.path.isdir(extract_dir):
                shutil.rmtree(extract_dir)
            zip_ref.extractall(extract_dir)
            
        extractedDirs = os.listdir(extract_dir)
        extractedTopDir = os.path.join(extract_dir, extractedDirs[0]) if extractedDirs else extract_dir
        
        # This blocking function runs in thread pool
        processCodebaseFolder(extractedTopDir, index_name, namespace_name, branch)

    @staticmethod
    def _cleanup_files(zip_path: str, extract_dir: str):
        """Synchronous cleanup helper"""
        try:
            os.remove(zip_path)
        except OSError:
            pass
        try:
            shutil.rmtree(extract_dir)
        except OSError:
            pass


    @staticmethod
    async def downloadRepository(repo_url: str, projectId: int, categoryId: int, currentUser: dict, backgroundTasks: BackgroundTasks) -> dict:
        try:
            repoAllreadyExist = False
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            vectorNamespaceDetails = await VectorNamespaceRepository.findOneByClause({"id": categoryId})
            if not vectorNamespaceDetails:
                raise HTTPException(status_code=404, detail="Category not found")

            if not os.path.exists(GitHubService.ASSETS_DIR):
                os.makedirs(GitHubService.ASSETS_DIR)

            # Parse GitHub URL function (same as before)
            def parse_github_url(url: str):
                url = url.rstrip('/').removesuffix('.git')
                patterns = [
                    r'https://github\.com/([^/]+)/([^/]+)/tree/(.+)',
                    r'https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)',
                    r'https://github\.com/([^/]+)/([^/]+)/?$',
                    r'git@github\.com:([^/]+)/([^/]+)',
                    r'git://github\.com/([^/]+)/([^/]+)'
                ]
                
                for pattern in patterns:
                    match = re.match(pattern, url)
                    if match:
                        owner = match.group(1)
                        repo = match.group(2)
                        branch = match.group(3) if len(match.groups()) >= 3 else None
                        return owner, repo, branch
                
                raise ValueError("Invalid GitHub URL format")

            try:
                owner, repo, branch = parse_github_url(repo_url)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid GitHub URL: {str(e)}")

            # Create repo record
            repoDetails = await GithubRepoRepository.findOneByClause({
                "userId": currentUser.get("userId"), 
                "projectId": projectId, 
                "categoryId": categoryId
            })
            
            if repoDetails and repoDetails.repoName != repo:
                repoAllreadyExist = True
                raise HTTPException(status_code=400, detail="A different repository is already linked to this category. Please select another category.")
            
            repoDetails = await GithubRepoRepository.findOneByClause({
                "repoName": repo, 
                "repoOwner": owner, 
                "userId": currentUser.get("userId"), 
                "projectId": projectId, 
                "categoryId": categoryId
            })
            
            if not repoDetails:
                repoDetails = await GithubRepoRepository.create({
                    "userId": currentUser.get("userId"),
                    "repoName": repo,
                    "repoOwner": owner,
                    "repoUrl": repo_url,
                    "projectId": projectId,
                    "categoryId": categoryId,
                    "status": "uploading"
                })

            # Get default branch if not specified
            if not branch:
                async with httpx.AsyncClient() as client:
                    repo_info_response = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo}",
                        headers=await GitHubService.getHeaders(userId=currentUser.get("userId"))
                    )
                    if repo_info_response.status_code == 200:
                        repo_info = repo_info_response.json()
                        branch = repo_info.get("default_branch", "main")
                    else:
                        branch = "main"
            # Download URLs and paths
            download_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"

              # Create branch record
            branchDetails = await GithubBranchRepository.findOneByClause({
                "githubRepoId": repoDetails.id,
                "branchName": branch
            })
            if not branchDetails:
                branchDetails = await GithubBranchRepository.create({
                    "userId": currentUser.get("userId"),
                    "githubRepoId": repoDetails.id,
                    "branchName": branch,
                    "status": "uploading",
                    "branchRepoUrl": download_url
                })
                
            zip_filename = f"{owner}_{repo}_{branch}.zip"
            zip_path = os.path.join(GitHubService.ASSETS_DIR, zip_filename)
            extract_dir = os.path.join(GitHubService.ASSETS_DIR, f"{owner}_{repo}_{branch}")

            # Download the ZIP file
            with requests.get(download_url, headers=await GitHubService.getHeaders(userId=currentUser.get("userId")), stream=True) as r:
                if not r.ok:
                    raise HTTPException(status_code=404, detail="Repository or branch not found")
                r.raise_for_status()
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # ADD BACKGROUND TASK HERE - Run processing in background
           
            backgroundTasks.add_task(
                GitHubService.process_downloaded_repo,
                zip_path, extract_dir, projectIndexDetails.indexName,
                vectorNamespaceDetails.name, branch, repoDetails.id,
                currentUser.get("userId"), download_url
            )
            

            return {"message": "Code is being uploaded, please check back after few minutes"}

        except Exception as e:
            if 'repoDetails' in locals() and repoAllreadyExist == False:
                await GithubRepoRepository.updateByClause({"id": repoDetails.id}, status="failed")
            raise HTTPException(
                status_code=e.status_code if e.status_code else 500,
                detail=f"{str(e)}"
            )

    @staticmethod
    async def fetchFileContentAtRef(owner: str, repo: str, filePath: str, ref: str, currentUser: dict) -> Optional[str]:
        """Fetch file content with no timeout"""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filePath}"
            params = {"ref": ref}
            
            # No timeout - will wait indefinitely
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.get(
                    url,
                    headers=await GitHubService.getHeaders(userId=currentUser.get("userId")),
                    params=params
                )
                response.raise_for_status()
                
                fileData = response.json()
                
                if fileData.get("encoding") == "base64":
                    content = base64.b64decode(fileData["content"]).decode('utf-8')
                    return content
                else:
                    return fileData.get("content", "")
                    
        except httpx.HTTPStatusError as e:
            print(f"Error fetching file {filePath} at ref {ref}: {e}")
            return None


    @staticmethod
    async def fetchAndStorePrFiles(pr_url: str, projectId: int, categoryId: int, currentUser: dict, backgroundTasks: BackgroundTasks) -> bool:
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
             
            # Parse PR URL to extract owner, repo, and PR number
            def parse_pr_url(url: str):
                """Parse GitHub PR URL to extract owner, repo, and PR number"""
                # Pattern to match GitHub PR URLs
                patterns = [
                    # https://github.com/owner/repo/pull/123
                    r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)',
                    # https://github.com/owner/repo/pulls/123
                    r'https://github\.com/([^/]+)/([^/]+)/pulls/(\d+)'
                ]
                
                for pattern in patterns:
                    match = re.match(pattern, url.rstrip('/'))
                    if match:
                        owner = match.group(1)
                        repo = match.group(2)
                        pr_number = int(match.group(3))
                        return owner, repo, pr_number
                
                raise ValueError("Invalid GitHub PR URL format")

            try:
                owner, repo, prNumber = parse_pr_url(pr_url)
                githubRepoDetails = await GithubRepoRepository.findOneByClause({"repoName": repo, "repoOwner": owner, "userId": currentUser.get("userId"), "projectId": projectId, "categoryId": categoryId})
                if not githubRepoDetails:
                    raise HTTPException(status_code=404, detail="Repository not found")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid PR URL: {str(e)}")
            
            indexName = projectIndexDetails.indexName
            namespace = vectorNamespaceDetails.name
  
            async with httpx.AsyncClient() as client:
                prResponse = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/pulls/{prNumber}",
                    headers= await GitHubService.getHeaders(userId=currentUser.get("userId"))
                )
                prResponse.raise_for_status()
                prData = prResponse.json()
                
                pr_title = prData.get("title") or ""
            backgroundTasks.add_task(
                GitHubService.storePrFilesToVectorDb,
                        prUrl=pr_url,
                        indexName=indexName,
                        namespace=namespace,
                        currentUser=currentUser,
                        githubRepoId=githubRepoDetails.id,
                        prNumber=prNumber,
                        prName=pr_title,
            )
                    
        except httpx.HTTPStatusError as e:
            print(f"HTTP error processing PR: {e}")
            raise HTTPException(
                status_code=e.status_code if e.status_code else 500,
                detail=f"{str(e)}"
            )
        
    @staticmethod
    async def fetchAndStorePrFilesInBackground(indexName: str, namespace: str, 
                                            currentUser: dict, githubRepoId: str, 
                                            mergedPrs: list) -> bool:
        """
        Process multiple PRs in background - stays as async def
        """
        try:
            for i, pr in enumerate(mergedPrs, 1):
                pr_number = pr["number"]
                pr_title = pr.get("title", "")
                pr_url = pr["html_url"]
                
                print(f"Processing PR #{pr_number} ({i}/{len(mergedPrs)}): {pr_title}")
            
                await GitHubService.storePrFilesToVectorDb(
                    prUrl=pr_url,
                    indexName=indexName,
                    namespace=namespace,
                    currentUser=currentUser,
                    githubRepoId=githubRepoId,
                    prNumber=pr_number,
                    prName=pr_title,
                )
            return True  
        except Exception as e:
            raise HTTPException(
                status_code=e.status_code if e.status_code else 500,
                detail=f"{str(e)}"
            )

    @staticmethod
    async def storePrFilesToVectorDb(prUrl: str, indexName: str, namespace: str, 
                                    currentUser: dict, githubRepoId: str, 
                                    prNumber: int, prName: str) -> bool:
        """
        Fetch all files changed in a PR, chunk them, and store in vector DB
        """
        try:
            githubPrDetails = await GithubPullRequestRepository.findOneByClause({
                "userId": currentUser.get("userId"),
                "githubRepoId": githubRepoId,
                "prNumber": prNumber,
                "prUrl": prUrl,
                "prName": prName,
                })
            if githubPrDetails:
                return True
                
            githubPrDetails = await GithubPullRequestRepository.create({
                "userId": currentUser.get("userId"),
                "githubRepoId": githubRepoId,
                "prNumber": prNumber,
                "prUrl": prUrl,
                "prName": prName,
                "status": "uploading"
            })
                
            # Parse PR URL to extract owner, repo, and PR number
            def parse_pr_url(url: str):
                patterns = [
                    r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)',
                    r'https://github\.com/([^/]+)/([^/]+)/pulls/(\d+)'
                ]
                
                for pattern in patterns:
                    match = re.match(pattern, url.rstrip('/'))
                    if match:
                        owner = match.group(1)
                        repo = match.group(2)
                        pr_number = int(match.group(3))
                        return owner, repo, pr_number
                
                raise ValueError("Invalid GitHub PR URL format")

            try:
                owner, repo, prNumber = parse_pr_url(prUrl)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid PR URL: {str(e)}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Fetch PR files
                filesResponse = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/pulls/{prNumber}/files",
                    headers=await GitHubService.getHeaders(userId=currentUser.get("userId"))
                )
                filesResponse.raise_for_status()
                changedFiles = filesResponse.json()
                
                # Fetch PR details
                prResponse = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/pulls/{prNumber}",
                    headers=await GitHubService.getHeaders(userId=currentUser.get("userId"))
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
                    "date": prData.get("merged_at") or "",
                    "pr_url": prUrl
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
                        beforeContent = await GitHubService.fetchFileContentAtRef(
                            owner, repo, filePath, baseSha, currentUser
                        )
                        if beforeContent:
                            beforeMetadata = {
                                **fileMetadata,
                                "version_type": "pr_before",
                                "commit_sha": baseSha
                            }
                            
                            beforeFileName = f"{filePath}_pr{prNumber}_before"
                            
                            # CHANGED: Run CPU-intensive chunking in thread pool
                            loop = asyncio.get_running_loop()
                            beforeChunks = await loop.run_in_executor(
                                None,
                                chunkText,
                                beforeContent,
                                beforeMetadata,
                                beforeFileName
                            )
                            allChunks.extend(beforeChunks)
                    
                    if fileStatus != "removed":
                        afterContent = await GitHubService.fetchFileContentAtRef(
                            owner, repo, filePath, headSha, currentUser
                        )
                        if afterContent:
                            afterMetadata = {
                                **fileMetadata,
                                "version_type": "pr_after",
                                "commit_sha": headSha
                            }
                            
                            afterFileName = f"{filePath}_pr{prNumber}_after"
                            
                            # CHANGED: Run CPU-intensive chunking in thread pool
                            loop = asyncio.get_running_loop()
                            afterChunks = await loop.run_in_executor(
                                None,
                                chunkText,
                                afterContent,
                                afterMetadata,
                                afterFileName
                            )
                            allChunks.extend(afterChunks)
                
                if allChunks:
                    # CHANGED: Run blocking vector DB upsert in thread pool
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        upsertChunksOllama,
                        indexName,
                        namespace,
                        allChunks
                    )
                    print(f"Successfully stored {len(allChunks)} chunks for PR #{prNumber}")
                else:
                    print(f"No chunks to store for PR #{prNumber}")
            
            await GithubPullRequestRepository.updateByClause(
                {"id": githubPrDetails.id}, 
                status="active"
            )
            return True
                    
        except httpx.HTTPStatusError as e:
            print(f"HTTP error processing PR: {e}")
            await GithubPullRequestRepository.updateByClause(
                {"id": githubPrDetails.id}, 
                status="failed"
            )
            return False
        except Exception as e:
            if 'githubPrDetails' in locals():
                await GithubPullRequestRepository.updateByClause(
                    {"id": githubPrDetails.id}, 
                    status="failed"
                )
            print(f"Error processing PR: {e}")
            return False

    @staticmethod
    async def fetchAndStoreAllMergedPrs(repo_url: str, projectId: int, categoryId: int, currentUser: dict, backgroundTasks: BackgroundTasks) -> dict:
        """
        Fetch all merged PRs from a repository and store each one in the vector database
        """
        try:
            # Validate project and category exist
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            
            vectorIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectDetail.id})
            if not vectorIndexDetails:
                raise HTTPException(status_code=404, detail="Vector index not found")
            
            vectorNamespaceDetails = await VectorNamespaceRepository.findOneByClause({"id": categoryId})
            if not vectorNamespaceDetails:
                raise HTTPException(status_code=404, detail="Category not found")

            # Parse repository URL to extract owner and repo
            def parse_repo_url(url: str):
                """Parse GitHub repository URL to extract owner and repo"""
                # Remove trailing slash and .git extension if present
                url = url.rstrip('/').rstrip('.git')
                
                # Pattern to match GitHub URLs
                patterns = [
                    # https://github.com/owner/repo/tree/branch
                    r'https://github\.com/([^/]+)/([^/]+)/tree/',
                    # https://github.com/owner/repo/blob/branch/file
                    r'https://github\.com/([^/]+)/([^/]+)/blob/',
                    # https://github.com/owner/repo
                    r'https://github\.com/([^/]+)/([^/]+)/?$',
                    # git@github.com:owner/repo.git
                    r'git@github\.com:([^/]+)/([^/]+)',
                    # git://github.com/owner/repo.git
                    r'git://github\.com/([^/]+)/([^/]+)'
                ]
                
                for pattern in patterns:
                    match = re.match(pattern, url)
                    if match:
                        owner = match.group(1)
                        repo = match.group(2)
                        return owner, repo
                
                raise ValueError("Invalid GitHub repository URL format")

            try:
                owner, repo = parse_repo_url(repo_url)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid repository URL: {str(e)}")

            # Fetch all merged PRs with pagination
            all_merged_prs = []
            page = 1
            per_page = 100  # GitHub's max per page
            
            async with httpx.AsyncClient() as client:
                while True:
                    params = {
                        "state": "closed",
                        "sort": "updated",
                        "direction": "asc",
                        "page": page,
                        "per_page": per_page 
                    }
                    
                    response = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo}/pulls",
                        headers= await GitHubService.getHeaders(userId=currentUser.get("userId")),
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

            repoDetails = await GithubRepoRepository.findOneByClause({"repoName": repo, "repoOwner": owner, "userId": currentUser.get("userId"), "projectId": projectId, "categoryId": categoryId})
            if not repoDetails:
                raise HTTPException(status_code=404, detail="Repository not found")
            
            
            backgroundTasks.add_task(
                GitHubService.fetchAndStorePrFilesInBackground,
                indexName=vectorIndexDetails.indexName,
                namespace=vectorNamespaceDetails.name,
                currentUser=currentUser,
                githubRepoId=repoDetails.id,
                mergedPrs=all_merged_prs,
            )
                
                

            
            return {"message": "Code pull requests is being uploaded, please check back after few minutes"}

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to fetch PRs from repository: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing merged PRs: {str(e)}"
            )

    @staticmethod
    async def handleStoreGithubToken(githubToken: str, currentUser: dict) -> dict:
        try:
            tokenDetails = await GithubTokenRepository.findOneByClause({"userId": currentUser.get("userId")})
            if not tokenDetails:
                await GithubTokenRepository.create({
                    "userId": currentUser.get("userId"),
                    "token": githubToken
                })
                return {"status": "success", "message": "GitHub token stored successfully"}
            else:
                await GithubTokenRepository.updateByClause({"userId": currentUser.get("userId")}, token=githubToken)
                return {"status": "success", "message": "GitHub token updated successfully"}
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while storing github token: {str(e)}"
            )
            
    @staticmethod
    async def handleGetGithubToken(currentUser: dict) -> bool:
        try:
            tokenDetails = await GithubTokenRepository.findOneByClause({"userId": currentUser.get("userId")})
            if not tokenDetails:
                return False
            else:
                return True
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while fething github token: {str(e)}"
            )

    @staticmethod
    async def handleGetAllRepositories(currentUser: dict) -> dict:
        try:
            import httpx
            
            tokenDetails = await GithubTokenRepository.findOneByClause({"userId": currentUser.get("userId")})
            if not tokenDetails:
                raise HTTPException(
                    status_code=404,
                    detail="GitHub token not found"
                )
            
            token = tokenDetails.token
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with httpx.AsyncClient() as client:
                repo_response = await client.get(
                    "https://api.github.com/user/repos",
                    headers=headers,
                    params={
                        "affiliation": "owner,collaborator,organization_member",
                        "per_page": 100,  # Maximum per page
                        "sort": "updated",
                        "direction": "desc"
                    }
                )
                
                if repo_response.status_code != 200:
                    raise HTTPException(
                        status_code=repo_response.status_code,
                        detail=f"Failed to fetch repositories: {repo_response.text}"
                    )
                
                repositories = repo_response.json()
                result = []
                
                for repo in repositories:
                    repo_name = repo["name"]
                    repo_url = repo["html_url"]
                    repo_owner = repo["owner"]["login"]
                    
                    # Fetch branches for this repository
                    branches_response = await client.get(
                        f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches",
                        headers=headers,
                        params={"per_page": 100}
                    )
                    
                    branches_data = []
                    if branches_response.status_code == 200:
                        branches = branches_response.json()
                        branches_data = [
                            {
                                "name": branch["name"],
                                "url": f"{repo_url}/tree/{branch['name']}",
                                "commit_sha": branch["commit"]["sha"],
                                "commit_url": branch["commit"]["url"]
                            }
                            for branch in branches
                        ]
                    else:
                        # If branches fetch fails, continue with empty branches list
                        branches_data = []
                    
                    # Add repository info with branches
                    repo_info = {
                        "name": repo_name,
                        "full_name": repo["full_name"],
                        "url": repo_url,
                        "clone_url": repo["clone_url"],
                        "ssh_url": repo["ssh_url"],
                        "owner": repo_owner,
                        "private": repo["private"],
                        "description": repo["description"],
                        "default_branch": repo["default_branch"],
                        "branches": branches_data,
                        "branches_count": len(branches_data)
                    }
                    
                    result.append(repo_info)
            
            return {
                "success": True,
                "data": {
                    "repositories": result,
                    "total_count": len(result)
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while fetching repositories: {str(e)}"
            )

    from typing import List, Dict, Optional

    @staticmethod
    async def handleGetAllSyncedRepos(
        currentUser: Dict,
        projectId: Optional[int] = None,
        categoryId: Optional[int] = None,
        repoName: Optional[str] = None
    ) -> Dict:
        try:
            clause: Dict = {"userId": currentUser.get("userId")}
            if projectId:
                clause["projectId"] = projectId
            if categoryId:
                clause["categoryId"] = categoryId
            if repoName:
                clause["repoName__icontains"] = repoName

            repos = await GithubRepoRepository.findAllByClause(clause)
            if not repos:
                return {"repository": []}

            repo_ids = [r.id for r in repos]

            branches = await GithubBranchRepository.findAllByClause({"githubRepoId__in": repo_ids})
            pull_requests = await GithubPullRequestRepository.findAllByClause({"githubRepoId__in": repo_ids})

            branches_by_repo: Dict[int, List[Dict]] = {}
            for b in branches or []:
                rid = b.githubRepoId
                branches_by_repo.setdefault(rid, []).append({
                    "branchName": b.branchName,
                    "branchRepoUrl": b.branchRepoUrl,
                    "status": b.status,
                })

            prs_by_repo: Dict[int, List[Dict]] = {}
            for p in pull_requests or []:
                rid = p.githubRepoId
                prs_by_repo.setdefault(rid, []).append({
                    "prNumber": str(p.prNumber),
                    "prUrl": p.prUrl,
                    "prName": p.prName,
                    "status": p.status,
                })

            repository_payload: List[Dict] = []
            for r in repos:
                rid = r.id
                repository_payload.append({
                    "repoName": r.repoName,
                    "repoOwner": r.repoOwner,
                    "repoUrl": r.repoUrl,
                    "projectId": r.projectId,
                    "categoryId": r.categoryId,
                    "status": r.status,
                    "createdAt": r.createdAt.isoformat() if hasattr(r, 'createdAt') and r.createdAt else None,
                    "branches": branches_by_repo.get(rid, []),
                    "pullRequest": prs_by_repo.get(rid, [])
                })

            return {"repository": repository_payload}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while fetching repositories: {str(e)}"
            )



