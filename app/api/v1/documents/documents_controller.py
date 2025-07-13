"""API v1 controller for Documents."""
from typing import List
from fastapi import APIRouter, status, Form, UploadFile
from .document_service import DocumentService
from app.core.models.pydantic.document import ListDocumentDto

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description="Create a new document",
)
async def createDocument(projectId: int = Form(...), file: UploadFile = Form(...), categoryId: int = Form(...), metadata: str = Form(...)):
    document = await DocumentService.create(file, projectId, categoryId, metadata)
    return document

@router.get(
    "/{categoryId}",
    response_model=List[ListDocumentDto],
    description="Get all documents",
)
async def listDocuments(categoryId: int):
    return await DocumentService.handleListAllDocumentsByCategoryId(categoryId)
