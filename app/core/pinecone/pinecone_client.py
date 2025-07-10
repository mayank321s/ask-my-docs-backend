from pinecone import Pinecone

from os import getenv

pinecone = Pinecone(api_key=getenv("PINECONE_API_KEY"))


def upsertChunks(index, namespace, chunks):
    index = pinecone.Index(index)
    index.upsert_records(namespace, chunks)

def searchChunks(index, namespace, query, filters=None):
    index = pinecone.Index(index)
    return index.search(
        namespace=namespace,
        query={
            "top_k": 5,
            "inputs": {"text": query}
        },
        filter=filters
    )

def listNamespaces(index_name: str) -> list[str]:
    try:
        index = pinecone.Index(index_name)
        stats = index.describe_index_stats()
        return list(stats.get('namespaces', {}).keys())
    except Exception as e:
        print(f"Error listing namespaces for index {index_name}: {str(e)}")
        raise

def createIndex(index_name: str):
    pinecone.create_index_for_model(
        name=index_name,
        cloud="aws",
        region="us-east-1",
        embed={
            "model":"llama-text-embed-v2",
            "field_map":{"text": "chunk_text"}
        }
    )

def deleteIndex(index_name: str):
    if pinecone.has_index(index_name):
        pinecone.delete_index(index_name)

def listNamespaceRecords(index_name: str, namespace: str, limit: int = 1000) -> list[dict]:
    try:
        index = pinecone.Index(index_name)
        
        query_response = index.query(
            namespace=namespace,
            top_k=limit,
            include_values=True,
            include_metadata=True,
            vector=[0] * 1024
        )
        
        results = []
        for match in query_response.get('matches', []):
            result = {
                'id': match.id,
                'score': match.score,
                'values': match.values,
                'metadata': match.metadata or {}
            }
            results.append(result)
            
        return results
        
    except Exception as e:
        print(f"Error listing data in namespace {namespace} of index {index_name}: {str(e)}")
        raise