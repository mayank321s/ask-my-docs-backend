import os
import zipfile
import requests
from typing import Optional
import shutil
from fastapi import HTTPException
from urllib.parse import urljoin
import requests
import base64
from typing import Optional
from app.core.repository.project_repository import ProjectRepository
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from app.core.repository.github_token_repository import GithubTokenRepository
from app.core.qdrant.qdrant_client import ( upsertChunksOllama, processCodebaseFolder )
from app.core.chunker.chunker import chunkText
import re
import httpx

class GitHubService:
    GITHUB_API_BASE = "https://api.github.com"
    ASSETS_DIR = os.path.abspath("tempAssets")

    @staticmethod
    async def getHeaders(userId) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
        }
        tokenDetails = await GithubTokenRepository.findOneByClause({"userId": userId})
        if tokenDetails and tokenDetails.token:
            headers["Authorization"] = f"Bearer {tokenDetails.token}"
        return headers

    @staticmethod
    async def downloadRepository(repo_url: str, projectId: int, categoryId: int, currentUser: dict) -> bool:
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

            # Parse GitHub URL to extract owner, repo, and branch information
            def parse_github_url(url: str):
                """Parse GitHub URL to extract owner, repo, and branch"""
                # Remove trailing slash and .git extension if present
                url = url.rstrip('/').rstrip('.git')
                
                # Pattern to match GitHub URLs
                patterns = [
                    # https://github.com/owner/repo/tree/branch
                    r'https://github\.com/([^/]+)/([^/]+)/tree/(.+)',
                    # https://github.com/owner/repo/blob/branch/file
                    r'https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)',
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
                        branch = match.group(3) if len(match.groups()) >= 3 else None
                        return owner, repo, branch
                
                raise ValueError("Invalid GitHub URL format")

            try:
                owner, repo, branch = parse_github_url(repo_url)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid GitHub URL: {str(e)}")

            # If no branch specified, get the default branch from repository info
            if not branch:
                async with httpx.AsyncClient() as client:
                    repo_info_response = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo}",
                        headers=GitHubService.getHeaders(userId=currentUser.get("userId"))
                    )
                    if repo_info_response.status_code == 200:
                        repo_info = repo_info_response.json()
                        branch = repo_info.get("default_branch", "main")
                    else:
                        branch = "main"  # fallback to main

            # Construct the zipball download URL using GitHub API
            download_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"

            zip_filename = f"{owner}_{repo}_{branch}.zip"
            zip_path = os.path.join(GitHubService.ASSETS_DIR, zip_filename)
            extract_dir = os.path.join(GitHubService.ASSETS_DIR, f"{owner}_{repo}_{branch}")

            # Download the repository as ZIP
            async with httpx.AsyncClient() as client:
                async with client.stream('GET', download_url, 
                                    headers=GitHubService.getHeaders(userId=currentUser.get("userId"))) as response:
                    response.raise_for_status()
                    
                    with open(zip_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)

            # Extract the ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if os.path.isdir(extract_dir):
                    shutil.rmtree(extract_dir)

                zip_ref.extractall(extract_dir)

                # GitHub zipballs create a top-level directory with format owner-repo-commit
                extracted_dirs = os.listdir(extract_dir)
                if extracted_dirs:
                    extracted_top_dir = os.path.join(extract_dir, extracted_dirs[0])
                else:
                    extracted_top_dir = extract_dir

                # Process the codebase
                processCodebaseFolder(extracted_top_dir, projectIndexDetails.indexName, 
                                    vectorNamespaceDetails.name, branch)

            # Cleanup: remove ZIP file and extracted directory
            try:
                os.remove(zip_path)
            except OSError as e:
                print(f"Warning: Could not delete ZIP file {zip_path}: {e}")
            
            try:
                shutil.rmtree(extract_dir)
            except OSError as e:
                print(f"Warning: Could not delete extract directory {extract_dir}: {e}")
            
            return True

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to download repository: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while processing the repository: {str(e)}"
            )

    @staticmethod
    async def fetchFileContentAtRef(owner: str, repo: str, filePath: str, ref: str, currentUser: dict) -> Optional[str]:
        """
        Fetch file content at a specific commit/ref
        """
        try:
            url = f"repos/{owner}/{repo}/contents/{filePath}"
            params = {"ref": ref}
            
            response = requests.get(
                urljoin(GitHubService.GITHUB_API_BASE, url),
                headers=GitHubService.getHeaders(userId=currentUser.get("userId")),
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
    async def fetchAndStorePrFiles(pr_url: str, projectId: int, categoryId: int, currentUser: dict) -> bool:
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
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid PR URL: {str(e)}")
            
            indexName = projectIndexDetails.indexName
            namespace = vectorNamespaceDetails.name
            
            async with httpx.AsyncClient() as client:
                # Fetch PR files
                filesResponse = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/pulls/{prNumber}/files",
                    headers=GitHubService.getHeaders(userId=currentUser.get("userId"))
                )
                filesResponse.raise_for_status()
                changedFiles = filesResponse.json()
                
                # Fetch PR details
                prResponse = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/pulls/{prNumber}",
                    headers=GitHubService.getHeaders(userId=currentUser.get("userId"))
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
                    "pr_url": pr_url
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
                    
                    if fileStatus != "removed":
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
                    upsertChunksOllama(indexName, namespace, allChunks)
                    print(f"Successfully stored {len(allChunks)} chunks for PR #{prNumber}")
                    return True
                else:
                    print(f"No chunks to store for PR #{prNumber}")
                    return False
                    
        except httpx.HTTPStatusError as e:
            print(f"HTTP error processing PR: {e}")
            return False
        except Exception as e:
            print(f"Error processing PR: {e}")
            return False

    @staticmethod
    async def fetchAndStoreAllMergedPrs(repo_url: str, projectId: int, categoryId: int, currentUser: dict) -> dict:
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
                        headers=GitHubService.getHeaders(userId=currentUser.get("userId")),
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
                pr_url = pr["html_url"]  # Use the actual PR URL from API response
                
                print(f"Processing PR #{pr_number} ({i}/{len(all_merged_prs)}): {pr_title}")
                
                try:
                    success = await GitHubService.fetchAndStorePrFiles(
                        pr_url=pr_url,
                        projectId=projectId,
                        categoryId=categoryId,
                        currentUser=currentUser
                    )
                    
                    if success:
                        successful_prs.append({
                            "pr_number": pr_number,
                            "title": pr_title,
                            "merged_at": pr.get("merged_at"),
                            "pr_url": pr_url
                        })
                        print(f"✅ Successfully processed PR #{pr_number}")
                    else:
                        failed_prs.append({
                            "pr_number": pr_number,
                            "title": pr_title,
                            "error": "No chunks generated",
                            "pr_url": pr_url
                        })
                        print(f"⚠️  PR #{pr_number} processed but no chunks generated")
                        
                except Exception as e:
                    failed_prs.append({
                        "pr_number": pr_number,
                        "title": pr_title,
                        "error": str(e),
                        "pr_url": pr_url
                    })
                    print(f"❌ Failed to process PR #{pr_number}: {e}")
                    continue  # Continue with next PR even if one fails

            # Return summary
            result = {
                "repository": f"{owner}/{repo}",
                "repo_url": repo_url,
                "total_merged_prs": len(all_merged_prs),
                "successful_prs": len(successful_prs),
                "failed_prs": len(failed_prs),
                "successful_pr_details": successful_prs,
                "failed_pr_details": failed_prs
            }
            
            print(f"\n📊 Processing Summary:")
            print(f"Repository: {owner}/{repo}")
            print(f"Total merged PRs found: {result['total_merged_prs']}")
            print(f"Successfully processed: {result['successful_prs']}")
            print(f"Failed to process: {result['failed_prs']}")
            
            return result

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
                await GithubTokenRepository.update(tokenDetails.id, githubToken)
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

            


