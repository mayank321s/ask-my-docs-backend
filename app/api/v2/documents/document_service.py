"""Service layer for Project operations (API v1)."""

from app.core.repository.project_repository import ProjectRepository
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from fastapi import HTTPException
from tortoise.transactions import in_transaction
from app.core.qdrant.qdrant_client import upsertChunksOllama
from app.core.repository.document_repository import DocumentRepository
from app.core.chunker.chunker import chunkText
from app.utils.common import (
    extractTextFromPdf,
    extractTextFromDocx,
)
from app.core.repository.vector_chunks_repository import VectorChunkRepository
from fastapi import UploadFile
import json
from app.core.models.pydantic.document import ListDocumentDto
from datetime import datetime
from fastapi import BackgroundTasks
class DocumentService:
    @staticmethod
    async def handleUploadDocument(file: UploadFile, projectId: int, categoryId: int, metadata: str, backgroundTasks: BackgroundTasks):
        try:
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            vectorNamespaceDetails = await VectorNamespaceRepository.findOneByClause({"id": categoryId})

            backgroundTasks.add_task(
                DocumentService.uploadDocumentInBackground,
                file,
                metadata,
                projectIndexDetails.name,
                vectorNamespaceDetails.name,
                categoryId
            )

            return {"message": "Document is being processed. Please check back in a few minutes."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    async def uploadDocumentInBackground(file: UploadFile, metadata: str, projectIndexName: str, vectorNamespaceName: str, vectorNamespaceId: int):
        try:
            # Get the document to check if it exists
            metadata = json.loads(metadata)
            fileMetadata = {
                **metadata,
                "file_name": file.filename,
                "uploaded_at": datetime.now().isoformat()
            }
            filename_lower = file.filename.lower()
            if filename_lower.endswith(".pdf"):
                text = extractTextFromPdf(file)
            elif filename_lower.endswith(".docx"):
                text = extractTextFromDocx(file)
            else:
                text = file.file.read().decode(errors="ignore")
            chunks = chunkText(text, fileMetadata, file.filename)
            
            chunk_ids = [chunk["_id"] for chunk in chunks]
            
            async with in_transaction():
                upsertChunksOllama(projectIndexName, vectorNamespaceName, chunks)
                documentDetail = await DocumentRepository.create({
                    "name": file.filename,
                    "namespaceId": vectorNamespaceId,
                })
                await VectorChunkRepository.create({
                    "documentId": documentDetail.id,
                    "chunkIds": chunk_ids,
                    "metadata": metadata
                })
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        


    
        
    @staticmethod
    async def handleListAllDocumentsByCategoryId(categoryId: int):
        try:
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
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
    @staticmethod
    async def handleDeleteDocument(documentId: int):
        try:
            # Verify document exists
            documentDetail = await DocumentRepository.findOneByClause({"id": documentId})
            if not documentDetail:
                raise HTTPException(status_code=404, detail="Document not found")

            documentChunks = await VectorChunkRepository.findAllByClause({"documentId": documentId})
            chunk_ids = [chunk.id for chunk in documentChunks] if documentChunks else []

            # Delete in a single transaction
            async with in_transaction():
                # Delete chunks first (children before parent)
                if chunk_ids:
                    await VectorChunkRepository.deleteBulkByIds(chunk_ids)
                
                # Delete the document
                await DocumentRepository.deleteByClause({"id": documentId})

            return True

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
