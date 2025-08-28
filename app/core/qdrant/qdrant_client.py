# pip install qdrant-client ollama numpy
from qdrant_client import QdrantClient, models
import ollama
import os
import numpy as np
from app.core.chunker.chunker import chunkText  # your existing chunker
import uuid

# Initialize Qdrant client
qdrant = QdrantClient(url="http://localhost:6333")  # adjust host/port as needed

def upsert_chunks(collection_name, namespace, chunks, batch_size=50):
    """
    Upsert chunks to Qdrant in batches
    """
    if not chunks:
        return True
    
    # Convert chunks to Qdrant points
    points = []
    for chunk in chunks:
        # Add namespace to payload for filtering
        payload = {
            'chunk_text': chunk['chunk_text'],
            'namespace': namespace,  # replaces Pinecone namespace
            **{k: v for k, v in chunk.items() if k not in ['_id', 'chunk_text']}
        }
        
        points.append(models.PointStruct(
            id=chunk['_id'],
            vector=chunk['values'],  # assume 'values' contains the embedding
            payload=payload
        ))
    
    # Upload in batches
    if len(points) <= batch_size:
        qdrant.upsert(collection_name=collection_name, points=points)
        print(f"Upserted {len(points)} chunks in single batch")
        return True
    
    total_batches = (len(points) + batch_size - 1) // batch_size
    
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        batch_number = i // batch_size + 1
        
        try:
            qdrant.upsert(collection_name=collection_name, points=batch)
            print(f"Upserted batch {batch_number}/{total_batches}: {len(batch)} chunks")
        except Exception as e:
            print(f"Error upserting batch {batch_number}: {e}")
            raise
    
    print(f"Successfully upserted all {len(points)} chunks in {total_batches} batches")
    return True

def upsertChunksOllama(collection_name, namespace, chunks, batch_size=50):
    """
    Upsert chunks to Qdrant with locally generated embeddings
    """
    if not chunks:
        return True
    
    print("Generating embeddings locally...")
    points = []
    
    for chunk in chunks:
        # Generate embedding using local Ollama
        response = ollama.embed(
            model='nomic-embed-text',
            input=chunk['chunk_text']
        )
        
        # Prepare point for Qdrant
        payload = {
            'chunk_text': chunk['chunk_text'],
            'namespace': namespace,
            **{k: v for k, v in chunk.items() if k not in ['_id', 'chunk_text']}
        }
        
        points.append(models.PointStruct(
            id=chunk['_id'],
            vector=response['embeddings'][0],
            payload=payload
        ))
    
    # Upload in batches (same logic as above)
    if len(points) <= batch_size:
        qdrant.upsert(collection_name=collection_name, points=points)
        print(f"Upserted {len(points)} chunks in single batch")
        return True
    
    total_batches = (len(points) + batch_size - 1) // batch_size
    
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        batch_number = i // batch_size + 1
        
        try:
            qdrant.upsert(collection_name=collection_name, points=batch)
            print(f"Upserted batch {batch_number}/{total_batches}: {len(batch)} chunks")
        except Exception as e:
            print(f"Error upserting batch {batch_number}: {e}")
            raise
    
    print(f"Successfully upserted all {len(points)} chunks in {total_batches} batches")
    return True

def search_chunks(collection_name, namespace, query, filters=None):
    """
    Search chunks using Qdrant's inference API (if available) or provide query vector directly
    """
    # Build filter for namespace
    namespace_filter = models.Filter(
        must=[models.FieldCondition(key="namespace", match=models.MatchValue(value=namespace))]
    )
    
    # Combine with additional filters if provided
    if filters:
        # Merge filters - you may need to adjust this based on your filter structure
        if hasattr(filters, 'must'):
            namespace_filter.must.extend(filters.must if isinstance(filters.must, list) else [filters.must])
        else:
            # Handle simple filter cases
            namespace_filter.must.append(filters)
    
    # Note: This assumes you have a query vector. If using Qdrant's inference API, adjust accordingly
    # For now, we'll assume you pass the query as a vector or handle embedding separately
    search_params = {
        "collection_name": collection_name,
        "query_vector": query if isinstance(query, list) else None,  # Adjust based on your input
        "limit": 7,
        "query_filter": namespace_filter,
    }
    
    return qdrant.search(**search_params)

def searchChunksOllama(collection_name, namespace, query, filters=None):
    """
    Search chunks with locally generated query embedding
    """
    try:
        # Generate query embedding using local Ollama
        print(f"Generating embedding for query: {query}")
        response = ollama.embed(
            model='nomic-embed-text',
            input=query
        )
        query_embedding = response['embeddings'][0]
        print(query_embedding)
        
        # Build namespace filter
        namespace_filter = models.Filter(
            must=[models.FieldCondition(key="namespace", match=models.MatchValue(value=namespace))]
        )
        
        # Combine with additional filters
        if filters:
            # Convert Pinecone-style filters to Qdrant format if needed
            if isinstance(filters, dict):
                for key, value in filters.items():
                    namespace_filter.must.append(
                        models.FieldCondition(key=key, match=models.MatchValue(value=value))
                    )
        
        # Perform the search
        results = qdrant.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=7,
            query_filter=namespace_filter,
        )
        
        print(f"Found {len(results)} matches")
        return results
        
    except Exception as e:
        print(f"Error searching chunks in namespace {namespace}: {str(e)}")
        raise

def list_namespaces(collection_name: str) -> list[str]:
    """
    List unique namespace values in a collection (simulates Pinecone namespaces)
    """
    try:
        # Scroll through collection to find unique namespace values
        namespaces = set()
        
        # Use scroll to get all points (adjust limit as needed)
        scroll_result = qdrant.scroll(
            collection_name=collection_name,
            limit=10000,  # Adjust based on your collection size
            with_payload=True,
            with_vectors=False
        )
        
        for point in scroll_result[0]:  # scroll returns (points, next_page_offset)
            if point.payload and 'namespace' in point.payload:
                namespaces.add(point.payload['namespace'])
        
        return list(namespaces)
        
    except Exception as e:
        print(f"Error listing namespaces for collection {collection_name}: {str(e)}")
        raise

def createCollection(collection_name: str, dimension: int = 768):
    """
    Create Qdrant collection (equivalent to Pinecone index)
    """
    try:
        existing_collections = qdrant.get_collections()
        if any(col.name == collection_name for col in existing_collections.collections):
            print(f"Collection {collection_name} already exists")
            return
        
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=dimension,
                distance=models.Distance.COSINE
            )
        )
        print(f"Created collection: {collection_name}")
        
    except Exception as e:
        print(f"Error creating collection {collection_name}: {e}")
        raise

def create_collection_with_local_embeddings(collection_name: str, dimension: int = 768):
    """
    Same as create_collection since Qdrant doesn't distinguish between local/remote embeddings at collection level
    """
    return createCollection(collection_name, dimension)

def list_namespace_records(collection_name: str, namespace: str, limit: int = 1000) -> list[dict]:
    """
    List records in a specific namespace (using payload filtering)
    """
    try:
        namespace_filter = models.Filter(
            must=[models.FieldCondition(key="namespace", match=models.MatchValue(value=namespace))]
        )
        
        # Scroll through filtered results
        results = []
        offset = None
        
        while len(results) < limit:
            remaining = limit - len(results)
            scroll_result = qdrant.scroll(
                collection_name=collection_name,
                scroll_filter=namespace_filter,
                limit=min(remaining, 100),  # Batch size
                offset=offset,
                with_payload=True,
                with_vectors=True
            )
            
            points, next_offset = scroll_result
            
            for point in points:
                result = {
                    'id': point.id,
                    'score': 1.0,  # Scroll doesn't provide scores
                    'values': point.vector,
                    'metadata': point.payload or {}
                }
                results.append(result)
            
            if next_offset is None or len(points) == 0:
                break
                
            offset = next_offset
        
        return results[:limit]
        
    except Exception as e:
        print(f"Error listing data in namespace {namespace} of collection {collection_name}: {str(e)}")
        raise

def deleteCollection(collection_name: str):
    """
    Delete Qdrant collection (equivalent to Pinecone delete index)
    """
    try:
        existing_collections = qdrant.get_collections()
        if any(col.name == collection_name for col in existing_collections.collections):
            qdrant.delete_collection(collection_name=collection_name)
            print(f"Deleted collection: {collection_name}")
        else:
            print(f"Collection {collection_name} does not exist")
    except Exception as e:
        print(f"Error deleting collection {collection_name}: {e}")
        raise

def createNamespace(collection_name: str, namespace: str, project_name: str):
    """
    Create namespace by inserting a placeholder point (Qdrant uses payload filtering)
    """
    try:
        # Check if namespace already has points
        existing_namespaces = list_namespaces(collection_name)
        if namespace in existing_namespaces:
            print(f"Namespace '{namespace}' already exists in collection '{collection_name}'.")
            return
        
        # Create placeholder point
        response = ollama.embed(
            model='nomic-embed-text',
            input=f"This is a Category namespace for {project_name}."
        )
        
        # Generate a deterministic UUID based on namespace for consistency
        namespace_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"namespace_{namespace}_{project_name}"))
        
        placeholder_point = models.PointStruct(
            id=namespace_uuid,  # Use UUID instead of string
            vector=response['embeddings'][0],
            payload={
                "kind": "namespace-placeholder",
                "namespace": namespace,
                "project": project_name,
                "chunk_text": f"This is a Category namespace for {project_name}.",
                "created_for": project_name
            }
        )
        
        qdrant.upsert(collection_name=collection_name, points=[placeholder_point])
        print(f"Namespace '{namespace}' created in collection '{collection_name}' for project '{project_name}'.")
        
    except Exception as e:
        print(f"Error creating namespace {namespace}: {e}")
        raise

def processCodebaseFolder(root_folder: str, collection_name: str, namespace: str, branch_name: str):
    """
    Process codebase folder and upsert to Qdrant
    """
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
                    "branch_name": branch_name
                }

                # Chunk the file
                chunks = chunkText(file_text, metadata, file_name=filename)
                if not chunks:
                    print(f"Skipping {rel_filepath}: no chunks")
                    continue

                # Upsert chunks using Ollama embeddings
                upsertChunksOllama(collection_name, namespace, chunks)
                print(f"Upserted {len(chunks)} chunks from {rel_filepath}")

    except Exception as e:
        print(f"Error processing codebase folder: {e}")
        raise
