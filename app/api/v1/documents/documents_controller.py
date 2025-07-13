"""API v1 controller for Documents."""
from typing import List

from fastapi import APIRouter, status, Form, UploadFile

from .document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    description="Create a new document",
)
async def createDocument(projectId: int = Form(...), file: UploadFile = Form(...), categoryId: int = Form(...), metadata: str = Form(...)):
    document = await DocumentService.create(file, projectId, categoryId, metadata)
    return document