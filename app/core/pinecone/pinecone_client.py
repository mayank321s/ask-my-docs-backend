from pinecone import Pinecone

pinecone = Pinecone(api_key="")


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

def listNamespaces(index):
    stats = pinecone.Index(index).describe_index_stats()
    return list(stats['namespaces'].keys())

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