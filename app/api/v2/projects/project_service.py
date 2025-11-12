"""Service layer for Project operations (API v1)."""

from argparse import Namespace
from typing import Dict, List, Optional
from app.core.models.pydantic.document import ListDocumentDto
from app.core.repository.github_branch_repository import GithubBranchRepository
from app.core.repository.github_pull_request_repository import GithubPullRequestRepository
from app.core.repository.github_repo_repository import GithubRepoRepository
from app.core.repository.project_repository import ProjectRepository
from app.core.repository.document_repository import DocumentRepository
from app.core.repository.vector_chunks_repository import VectorChunkRepository
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.models.pydantic.projects import CreateProjectRequestDto, ListProjectDto
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from app.core.models.pydantic.category import CreateCategoryRequestDto, ListCategoryDto
from fastapi import HTTPException
from app.utils.common import convertStringToHyphen, getPaginationResponse
from tortoise.transactions import in_transaction
from app.core.qdrant.qdrant_client import createCollection, createNamespace, deleteCollection, deleteCategory

class ProjectService:
    """Provides CRUD operations for Projects for API v1."""

    @staticmethod
    async def create(request: CreateProjectRequestDto, user: dict):
        try:
            existing = await ProjectRepository.findOneByClause({"name": request.name, "userId": user.get("userId")})
            if existing:
                raise HTTPException(status_code=409, detail="Project with this name already exists")

            async with in_transaction():
                projectDetail = await ProjectRepository.create({"name": request.name, "userId": user.get("userId")})
                projectIndexName = convertStringToHyphen(request.name)
                
                createCollection(projectIndexName)
                await VectorIndexRepository.create({"indexName": projectIndexName, "projectId": projectDetail.id})

            return True
        except Exception as e:
            projectIndexName = convertStringToHyphen(request.name)
            if projectIndexName:
                deleteCollection(projectIndexName)
            raise HTTPException(status_code=500, detail=str(e))
        
    @staticmethod
    async def handleListAllProjects(user: dict, page: int, limit: int)-> dict:
        """Return all projects with their associated vector index name."""
        try:
            offset = (page -1 ) * limit
            if user.get("roleCode") == "user":
                projects_details, totalCount = await ProjectRepository.findAllByClause(
                    {
                    "userId": user.get("userId")
                    },
                    offset=offset,
                    limit=limit,
                )
            else:
                projects_details, totalCount = await ProjectRepository.list_all()
            result: list[ListProjectDto] = []
            for project in projects_details:
                indexDetails = await VectorIndexRepository.findOneByClause({"projectId": project.id})
                indexName = indexDetails.indexName if indexDetails else None

                result.append(
                    ListProjectDto(
                        id=project.id,
                        name=project.name,
                        indexName=indexName,
                        createdAt=project.createdAt,
                        updatedAt=project.updatedAt,
                    )
                )
            
            return {"data": result, 
                    "pagination": getPaginationResponse(totalCount, limit, page, len(projects_details)),
                    }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def handleCreateProjectCategory(projectId: int, request: CreateCategoryRequestDto):
        try:     
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            existing = await VectorNamespaceRepository.findOneByClause({"categoryName": request.name, "indexId": projectIndexDetails.id})
            if existing:
                raise HTTPException(status_code=409, detail="Category with this name already exists")

            async with in_transaction():
                namespace = convertStringToHyphen(request.name)
                createNamespace(projectIndexDetails.indexName, namespace, projectDetail.name)
                await VectorNamespaceRepository.create({"name": namespace, "categoryName": request.name, "indexId": projectIndexDetails.id})

            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @staticmethod
    async def handleListProjectCategoriesByProjectId(projectId: int):
        try:     
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            vectorNamespaceDetails = await VectorNamespaceRepository.findAllByClause({"indexId": projectIndexDetails.id})
            result: list[ListCategoryDto] = []
            for namespace in vectorNamespaceDetails:
                result.append(
                    ListCategoryDto(
                        id=namespace.id,
                        name=namespace.name,
                        categoryName=namespace.categoryName,
                        createdAt=namespace.createdAt,
                        updatedAt=namespace.updatedAt,
                    )
                )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @staticmethod
    async def handleDeleteProject(projectId: int, user: dict):
        try:
            # Validate project exists and belongs to user
            projectDetail = await ProjectRepository.findOneByClause({
                "id": projectId, 
                "userId": user.get("userId")
            })
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")

            # Get project index details
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            if not projectIndexDetails:
                raise HTTPException(status_code=404, detail="Project index not found")

            # Get all categories for this project
            projectCategories = await VectorNamespaceRepository.findAllByClause({"indexId": projectIndexDetails.id})
            
            if not projectCategories:
                # No categories, just delete index and project
                async with in_transaction():
                    await VectorIndexRepository.deleteByClause({"id": projectIndexDetails.id})
                    await ProjectRepository.deleteByClause({"id": projectId})
                deleteCollection(projectIndexDetails.indexName)
                return True

            # Collect all IDs for bulk deletion
            category_ids = [category.id for category in projectCategories]
            
            # Get all documents for all categories in one go (if possible with your schema)
            all_documents = []
            for category in projectCategories:
                documents = await DocumentRepository.findAllByClause({"namespaceId": category.id})
                all_documents.extend(documents)
            
            document_ids = [doc.id for doc in all_documents]
            
            # Get all chunks for all documents
            all_chunks = []
            if document_ids:
                # Bulk query for all chunks at once (assuming your repo supports this)
                for doc_id in document_ids:
                    chunks = await VectorChunkRepository.findAllByClause({"documentId": doc_id})
                    all_chunks.extend(chunks)
            
            chunk_ids = [chunk.id for chunk in all_chunks]

            # Perform all deletions in a single transaction
            async with in_transaction():
                # Delete in proper order (children first)
                if chunk_ids:
                    await VectorChunkRepository.deleteBulkByIds(chunk_ids)
                
                if document_ids:
                    await DocumentRepository.deleteBulkByIds(document_ids)
                
                if category_ids:
                    await VectorNamespaceRepository.deleteBulkByIds(category_ids)
                
                # Delete index and project
                await VectorIndexRepository.deleteByClause({"id": projectIndexDetails.id})
                await ProjectRepository.deleteByClause({"id": projectId})

            # Delete external collection (outside transaction)
            deleteCollection(projectIndexDetails.indexName)
            
            return True

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

        
    @staticmethod
    async def handleDeleteProjectCategory(projectId: int, categoryId: int, user: dict):
        try:
            projectDetail = await ProjectRepository.findOneByClause({
                "id": projectId, 
                "userId": user.get("userId")
            })
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")

            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            if not projectIndexDetails:
                raise HTTPException(status_code=404, detail="Project index not found")

            categoryDetail = await VectorNamespaceRepository.findOneByClause({
                "id": categoryId, 
                "indexId": projectIndexDetails.id
            })
            if not categoryDetail:
                raise HTTPException(status_code=404, detail="Category not found")

            categoryDocuments = await DocumentRepository.findAllByClause({
                "namespaceId": categoryId
            })
            
            document_ids = [doc.id for doc in categoryDocuments] if categoryDocuments else []


            chunk_ids = []
            if document_ids:
                for doc_id in document_ids:
                    chunks = await VectorChunkRepository.findAllByClause({"documentId": doc_id})
                    chunk_ids.extend([chunk.id for chunk in chunks] if chunks else [])

            async with in_transaction():
                if chunk_ids:
                    await VectorChunkRepository.deleteBulkByIds(chunk_ids)
                
                if document_ids:
                    await DocumentRepository.deleteBulkByIds(document_ids)
                
                await VectorNamespaceRepository.deleteByClause({"id": categoryDetail.id})
            deleteCategory(projectIndexDetails.indexName, categoryDetail.name)
            
            return True

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete category: {str(e)}")


    @staticmethod
    async def handleGetAllSyncedDataInCategory(
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

            repository_payload: List[Dict] = []
            repos = await GithubRepoRepository.findAllByClause(clause)
            if repos:
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
            documentsDetails = await DocumentRepository.findAllByClause({"namespaceId": categoryId})
            result: list[ListDocumentDto] = []
            for document in documentsDetails:

                result.append(
                    ListDocumentDto(
                        id=document.id,
                        name=document.name,
                        createdAt=document.createdAt,
                        updatedAt=document.updatedAt,
                    )
                )

            return {"repository": repository_payload, "documents": result}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while fetching repositories: {str(e)}"
            )



