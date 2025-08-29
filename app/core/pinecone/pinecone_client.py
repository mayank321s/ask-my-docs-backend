from pinecone import Pinecone, ServerlessSpec
from app.core.chunker.chunker import chunkText

from os import getenv
import os
import ollama

pinecone = Pinecone(api_key=getenv("PINECONE_API_KEY"))


def upsertChunks(index_name, namespace, chunks, batch_size=50):
    """
    Upsert chunks to Pinecone in batches to avoid exceeding batch size limits
    """
    if not chunks:
        return True
    
    index = pinecone.Index(index_name)
    
    # If chunks fit in a single batch, upload directly
    if len(chunks) <= batch_size:
        index.upsert_records(namespace, chunks)
        print(f"Upserted {len(chunks)} chunks in single batch")
        return True
    
    # Process large batches in smaller chunks
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_number = i // batch_size + 1
        
        try:
            index.upsert_records(namespace, batch)
            print(f"Upserted batch {batch_number}/{total_batches}: {len(batch)} chunks")
        except Exception as e:
            print(f"Error upserting batch {batch_number}: {e}")
            raise
    
    print(f"Successfully upserted all {len(chunks)} chunks in {total_batches} batches")
    return True


def upsertChunksOllama(index_name, namespace, chunks, batch_size=50):
    """
    Upsert chunks to Pinecone with locally generated embeddings
    """
    if not chunks:
        return True
    
    index = pinecone.Index(index_name)
    
    # Generate embeddings for all chunks
    print("Generating embeddings locally...")
    embedded_chunks = []
    
    for chunk in chunks:
        # Generate embedding using local Ollama
        response = ollama.embed(
            model='nomic-embed-text',
            input=chunk['chunk_text']
        )
        
        # Prepare vector for Pinecone
        embedded_chunk = {
            'id': chunk['_id'],
            'values': response['embeddings'][0],
            'metadata': {
                'chunk_text': chunk['chunk_text'],
                **{k: v for k, v in chunk.items() if k not in ['_id', 'chunk_text']}
            }
        }
        embedded_chunks.append(embedded_chunk)
    
    # Upload in batches (same logic as before)
    if len(embedded_chunks) <= batch_size:
        index.upsert(vectors=embedded_chunks, namespace=namespace)
        print(f"Upserted {len(embedded_chunks)} chunks in single batch")
        return True
    
    total_batches = (len(embedded_chunks) + batch_size - 1) // batch_size
    
    for i in range(0, len(embedded_chunks), batch_size):
        batch = embedded_chunks[i:i + batch_size]
        batch_number = i // batch_size + 1
        
        try:
            index.upsert(vectors=batch, namespace=namespace)
            print(f"Upserted batch {batch_number}/{total_batches}: {len(batch)} chunks")
        except Exception as e:
            print(f"Error upserting batch {batch_number}: {e}")
            raise
    
    print(f"Successfully upserted all {len(embedded_chunks)} chunks in {total_batches} batches")
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

def createIndexWithLocalEmbeddings(indexName: str):
    pinecone.create_index(
        name=indexName,
        dimension=768,
        metric='cosine',
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
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

def createNamespacOllama(indexName: str, namespace: str, projectName: str, dim: int = 768):
    """
    For client-side embeddings indexes: create a namespace implicitly by upserting
    a minimal vector. Namespaces are auto-created on first upsert.
    """
    index = pinecone.Index(indexName)

    stats = index.describe_index_stats()
    if namespace in stats.get("namespaces", {}):
        print(f"Namespace '{namespace}' already exists in index '{indexName}'.")
        return

    emb = ollama.embed(model="nomic-embed-text", input=f"Category namespace for {projectName}.")["embeddings"][0]

    index.upsert(
        vectors=[{
            "id": f"__ns__{namespace}",
            "values": emb,
            "metadata": {
                "kind": "namespace-placeholder",
                "project": projectName,
            }
        }],
        namespace=namespace
    )
    print(f"Namespace '{namespace}' created in index '{indexName}' for project '{projectName}'.")


def processCodebaseFolder(root_folder: str, pinecone_index, namespace: str, branchName: str):
    try:
        for dirpath, _, filenames in os.walk(root_folder):
            for filename in filenames:
                abs_filepath = os.path.join(dirpath, filename)
                rel_filepath = os.path.relpath(abs_filepath, root_folder).replace("\\", "/")

                # Try to read the file
                try:
                    with open(abs_filepath, "r", encoding="utf-8") as f:
                        file_text = f.read()
                except Exception as e:
                    print(f"Skipping {abs_filepath}: {e}")
                    continue

                # Prepare metadata
                metadata = {
                    "file_name": filename,
                    "relative_path": rel_filepath,
                    "branch_name": branchName
                }

                # Chunk the file
                chunks = chunkText(file_text, metadata, file_name=filename)
                if not chunks:       # nothing to upload
                    print(f"Skipping {rel_filepath}: no chunks")
                    continue

                # Upsert chunks
                upsertChunks(pinecone_index, namespace, chunks)
                print(f"Upserted {len(chunks)} chunks from {rel_filepath}")

    except Exception as e:
        print(f"Error processing codebase folder: {e}")
        raise

def searchChunksOllama(index: str, namespace: str, query: str, filters=None):
    try:
        # Generate query embedding using local Ollama
        print(f"Generating embedding for query: {query}")
        response = ollama.embed(
            model='nomic-embed-text',
            input=query
        )
        query_embedding = response['embeddings'][0]
        
        pineconeIndex = pinecone.Index(index)
        
        # Prepare search parameters
        search_params = {
            "vector": query_embedding,
            "top_k": 7,
            "include_metadata": True,
            "include_values": False,
            "namespace": namespace
        }
        
        # Add filters if provided
        if filters is not None:
            search_params["filter"] = filters
        
        # Perform the search
        results = pineconeIndex.query(**search_params)
        
        print(f"Found {len(results.get('matches', []))} matches")
        return results
        
    except Exception as e:
        print(f"Error searching chunks in namespace {namespace}: {str(e)}")
        raise
