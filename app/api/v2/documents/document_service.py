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
class DocumentService:
    @staticmethod
    async def handleUploadDocument(file: UploadFile, projectId: int, categoryId: int, metadata: str):
        try:
            projectDetail = await ProjectRepository.get_by_id(projectId)
            if not projectDetail:
                raise HTTPException(status_code=404, detail="Project not found")
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": projectId})
            vectorNamespaceDetails = await VectorNamespaceRepository.findOneByClause({"id": categoryId})
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
                # treat as plain text
                text = file.file.read().decode(errors="ignore")
            chunks = chunkText(text, fileMetadata, file.filename)
            async with in_transaction():
                upsertChunksOllama(projectIndexDetails.indexName, vectorNamespaceDetails.name, chunks)
                 # Step 2: Create document entry
                documentDetail = await DocumentRepository.create({
                    "name": file.filename,
                    "namespaceId": vectorNamespaceDetails.id,
                })

                # Step 3: Insert each chunk record
                for chunk in chunks:
                    await VectorChunkRepository.create({
                        "documentId": documentDetail.id,
                        "chunkId": chunk["_id"],
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