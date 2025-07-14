from pinecone import Pinecone

from os import getenv

pinecone = Pinecone(api_key="pcsk_5reQKK_NsVxjifLzB5xjYsrPkB3EfNdRwhAJCKcZzUU82FWoPa1VZXGPqPdVRgz9XvJgbN")


def upsertChunks(index, namespace, chunks):
    index = pinecone.Index(index)
    index.upsert_records(namespace, chunks)
    return True

def searchChunks(index, namespace, query, filters=None):
    index = pinecone.Index(index)
    searchParams = {
        "namespace": namespace,
        "query": {
            "top_k": 7,
            "inputs": {"text": query}
        }
    }
    if filters is not None:
        searchParams["filter"] = filters

    return index.search(**searchParams)

def listNamespaces(index_name: str) -> list[str]:
    try:
        index = pinecone.Index(index_name)
        stats = index.describe_index_stats()
        return list(stats.get('namespaces', {}).keys())
    except Exception as e:
        print(f"Error listing namespaces for index {index_name}: {str(e)}")
        raise

def createIndex(indexName: str):
    pinecone.create_index_for_model(
        name=indexName,
        cloud="aws",
        region="us-east-1",
        embed={
            "model":"llama-text-embed-v2",
            "field_map":{"text": "chunk_text"}
        }
    )

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

def deleteIndex(indexName: str):
    if pinecone.has_index(indexName):
        pinecone.delete_index(indexName)
        
def createNamespace(indexName: str, namespace: str, projectName: str):
    """
    Creates a namespace in the given index by inserting a placeholder record.
    This is required because Pinecone does not support explicit namespace creation.
    """
    index = pinecone.Index(indexName)

    existing_namespaces = index.describe_index_stats()["namespaces"]
    if namespace in existing_namespaces:
        print(f"Namespace '{namespace}' already exists in index '{indexName}'.")
        return

    dummy_vector = [{
        "_id": namespace,
        "chunk_text": f"This is a Category namespace for {projectName}.",
        "created_for": projectName
    }]
    
    index.upsert_records(namespace, dummy_vector)
    print(f"Namespace '{namespace}' created in index '{indexName}' for project '{projectName}'.")