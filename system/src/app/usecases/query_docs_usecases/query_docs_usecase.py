from system.src.app.config.settings import settings
from system.src.app.services.re_ranking_service import RerankerService
from system.src.app.usecases.query_docs_usecases.pinecone_query_usecase import PineconeQueryUseCase
from fastapi import Depends

class QueryDocsUsecase:
    def __init__(self,
        pinecone_query_usecase: PineconeQueryUseCase = Depends(PineconeQueryUseCase),
        reranker_service: RerankerService = Depends(RerankerService)
    ):
        self.pinecone_query_usecase = pinecone_query_usecase
        self.reranker_service = reranker_service

    async def query_docs(self, query: str, index_name: str, top_k: int = 20, is_hybrid: bool = True, alpha: float = 0.8, top_n: int = 5):
        pinecone_response = await self.pinecone_query_usecase.random_query(query, index_name, top_k, is_hybrid, alpha)
        filtered_docs = [
            chunk.get("content") for chunk in pinecone_response if chunk["score"] > 0.2
        ]
        if not filtered_docs:
            return []

        print(filtered_docs)

        reranked_results = await self.reranker_service.voyage_rerank(
            model_name=settings.VOYAGEAI_RERANKING_MODEL,
            query=query,
            documents=filtered_docs,
            top_n=top_n,
        )
        final_results = []
        for result in reranked_results.get("data", []):
            index = result.get("index")
            if index is not None and 0 <= index < len(filtered_docs):
                final_results.append(
                    {
                        "query": filtered_docs[index],
                        "relevance_score": result.get("relevance_score", 0),
                        "metadata": pinecone_response[index].get("metadata", {}),
                    }
                )

        return final_results
        