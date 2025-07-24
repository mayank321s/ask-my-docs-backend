from fastapi import HTTPException
from fastapi import status
from app.core.models.pydantic.chat import SearchAndAnswerRequestDto
from app.core.repository.vector_index_repository import VectorIndexRepository
from app.core.repository.vector_namespace_repository import VectorNamespaceRepository
from app.core.pinecone.pinecone_client import searchChunks
from app.core.llm.llm import askAzureMinistral, askOllamaLlm

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

                results = searchChunks(
                    index=projectIndexDetails.indexName,
                    namespace=namespaceDetails.name,
                    query=request.query
                )
                print(results)
                all_hits.extend(results['result']['hits'])
            else:
                namespaces = await VectorNamespaceRepository.findAllByClause({"indexId": projectIndexDetails.id})
                for ns in namespaces:
                    results = searchChunks(
                        index=projectIndexDetails.indexName,
                        namespace=ns.name,
                        query=request.query
                    )
                    print(results)
                    all_hits.extend(results['result']['hits'])

            # answer = askOllamaLlm(request.query, all_hits)
            return {"answer": ""}

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))