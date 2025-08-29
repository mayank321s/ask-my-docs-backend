from fastapi import HTTPException
from fastapi import status
from app.core.models.pydantic.chat import SearchAndAnswerRequestDto
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from app.core.pinecone.pinecone_client import searchChunksOllama
from app.core.qdrant.qdrant_client import searchChunksOllama
from app.core.llm.llm import askOllamaLlm, askHuggingFaceLLM


class ChatService:
    @staticmethod
    async def handleSearchAndAnswer(request: SearchAndAnswerRequestDto):
        try:
            projectIndexDetails = await VectorIndexRepository.findOneByClause({"projectId": request.projectId})
            if not projectIndexDetails:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project index not found")

            all_hits = []

            if request.categoryId:
                namespaceDetails = await VectorNamespaceRepository.findOneByClause({"id": request.categoryId})
                if not namespaceDetails:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Namespace not found")

                results = searchChunksOllama(
                    collection_name=projectIndexDetails.indexName,
                    namespace=namespaceDetails.name,
                    query=request.query
                )
                print(results)
                # Fix: results is already the list of ScoredPoint objects
                all_hits.extend(results)
            else:
                namespaces = await VectorNamespaceRepository.findAllByClause({"indexId": projectIndexDetails.id})
                for ns in namespaces:
                    results = searchChunksOllama(
                        collection_name=projectIndexDetails.indexName,
                        namespace=ns.name,
                        query=request.query
                    )
                    # Fix: results is already the list of ScoredPoint objects
                    all_hits.extend(results)

            # Transform ScoredPoint objects to the format askOllamaLlm expects
            formatted_hits = []
            for hit in all_hits:
                formatted_hit = {
                    "fields": hit.payload  # Convert ScoredPoint.payload to the expected format
                }
                formatted_hits.append(formatted_hit)

            # answer = askOllamaLlm(request.query, formatted_hits)
            answer = askHuggingFaceLLM(request.query, formatted_hits)
            return {"answer": answer}

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
