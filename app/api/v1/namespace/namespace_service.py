from typing import List, Dict, Any
from fastapi import HTTPException
from app.core.pinecone.pinecone_client import listNamespaces, listNamespaceRecords

class NamespaceService:
    """Service class for namespace operations"""

    @staticmethod
    async def list_namespaces(index_name: str) -> List[str]:
        try:
            return listNamespaces(index_name)
        except Exception as e:
            status_code = 400 if "not found" in str(e).lower() else 500
            raise HTTPException(
                status_code=status_code,
                detail=f"Failed to fetch namespaces for index '{index_name}': {str(e)}"
            )

    @staticmethod
    async def get_namespace_records(
        index_name: str,
        namespace: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        try:
            if limit < 1 or limit > 1000:
                raise ValueError("Limit must be between 1 and 1000")
            data = listNamespaceRecords(index_name, namespace, limit)
            return data
            
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            status_code = 400 if "not found" in str(e).lower() else 500
            raise HTTPException(
                status_code=status_code,
                detail=f"Failed to fetch records from namespace '{namespace}' in index '{index_name}': {str(e)}"
            )
