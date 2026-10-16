"""API v1 controller for Documents."""
from typing import List, Dict
from fastapi import APIRouter, status, Form, UploadFile, Depends, BackgroundTasks
from .document_service import DocumentService
from app.core.models.pydantic.document import ListDocumentDto
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    description="Upload a document to vector DB",
)
async def uploadDocumentOllama(backgroundTasks: BackgroundTasks, projectId: int = Form(...), file: UploadFile = Form(...), categoryId: int = Form(...), metadata: str = Form(...)):
    document = await DocumentService.handleUploadDocument(file, projectId, categoryId, metadata, backgroundTasks)
    return document



@router.get(
    "/{categoryId}",
    response_model=List[ListDocumentDto],
    description="Get all documents",
)
async def listDocuments(categoryId: int, currentUser: Dict = Depends(get_current_user)):
    return await DocumentService.handleListAllDocumentsByCategoryId(categoryId)

@router.delete(
    "/{documentId}",
    status_code=status.HTTP_200_OK,
    description="Delete a document by ID",
)
async def deleteDocument(documentId: int, currentUser: Dict = Depends(get_current_user)):
    return await DocumentService.handleDeleteDocument(documentId)