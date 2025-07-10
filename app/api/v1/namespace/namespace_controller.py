from fastapi import APIRouter, Query, Depends
from typing import List, Dict, Any
from app.api.v1.namespace.namespace_service import NamespaceService

router = APIRouter(prefix="/namespace", tags=["Namespace"])

@router.get("/{index_name}", response_model=List[str])
async def list_namespaces(index_name: str):
    return await NamespaceService.list_namespaces(index_name)

@router.get("/{index_name}/{namespace}/records", response_model=List[Dict[str, Any]])
async def get_namespace_records(
    index_name: str,
    namespace: str,
    limit: int = Query(1000, description="Maximum number of records to return", ge=1, le=1000)
):
    return await NamespaceService.get_namespace_records(index_name, namespace, limit)
