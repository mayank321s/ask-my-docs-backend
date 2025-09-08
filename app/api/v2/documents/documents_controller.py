"""API v1 controller for Documents."""
from typing import List, Dict
from fastapi import APIRouter, status, Form, UploadFile, Depends
from .document_service import DocumentService
from app.core.models.pydantic.document import ListDocumentDto
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    description="Upload a document to vector DB",
)
async def uploadDocumentOllama(projectId: int = Form(...), file: UploadFile = Form(...), categoryId: int = Form(...), metadata: str = Form(...), current_user: Dict = Depends(get_current_user)):
    document = await DocumentService.handleUploadDocument(file, projectId, categoryId, metadata, current_user)
    return document



@router.get(
    "/{categoryId}",
    response_model=List[ListDocumentDto],
    description="Get all documents",
)
async def listDocuments(categoryId: int, current_user: Dict = Depends(get_current_user)):
    return await DocumentService.handleListAllDocumentsByCategoryId(categoryId, current_user)
