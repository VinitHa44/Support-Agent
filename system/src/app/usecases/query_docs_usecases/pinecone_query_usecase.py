from fastapi import Depends, HTTPException, status

from system.src.app.config.settings import settings
from system.src.app.services.embedding_service import EmbeddingService
from system.src.app.services.pinecone_service import PineconeService
from system.src.app.utils.logging_utils import loggers


class PineconeQueryUseCase:

    def __init__(
        self,
        embedding_service: EmbeddingService = Depends(EmbeddingService),
        pinecone_service: PineconeService = Depends(PineconeService),
    ):
        self.embedding_service = embedding_service
        self.pinecone_service = pinecone_service
        self.embeddings_provider_mapping = {
            "llama-text-embed-v2": "pinecone",
            "multilingual-e5-large": "pinecone",
        }
        self.model_to_dimensions = {
            "llama-text-embed-v2": [1024, 2048, 768, 512, 384],
            "multilingual-e5-large": [1024],
        }

    async def _get_query_embeddings(self, query, embed_model, dimension):
        try:
            embedding_provider = self.embeddings_provider_mapping.get(
                embed_model
            )
            if embedding_provider == "pinecone":


                query_pinecone_response = await self.embedding_service.pinecone_dense_embeddings(
                    inputs=[query],
                    embedding_model=embed_model,
                    input_type="query",
                    dimension=dimension
                )
                # query_dense_embeds = [
                #     item["values"]
                #     for item in query_pinecone_response.get("data", [])
                # ]
                return query_pinecone_response[0]

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Embedding Model",
                )

        except Exception as e:
            loggers["main"].error(f"Error generating embedding {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error while generating the embeddings of querying docs: {str(e)}",
            )

    async def random_query(self, query, index_name, top_k=20, is_hybrid=True, alpha=0.8, categories=None):
        try:
            embed_model = "llama-text-embed-v2"
            dimension = 1024
            top_k = top_k
            is_hybrid = is_hybrid
            include_metadata = True
            namespace = "default"
            # if is_hybrid:
            index_name = index_name
            #     metric = "dotproduct"
            # else:
            #     index_name = settings.PINECONE_INDEX_NAME
            #     metric = "cosine"

            host = await self.pinecone_service.get_index_host(
                index_name=index_name
            )
            query_dense_vector = await self._get_query_embeddings(
                query, embed_model, dimension
            )

            # Prepare metadata filter if categories are provided
            metadata_filter = None
            if categories:
                metadata_filter = {"categories": {"$in": categories}}

            if is_hybrid:
                query_sparse_vector = (
                    self.embedding_service.pinecone_sparse_embeddings([query])
                )
                query_sparse_vector = query_sparse_vector[0]
                alpha = alpha
                loggers["main"].info(
                    "sparse embeddings generated in random query use case"
                )
                pinecone_response = (
                    await self.pinecone_service.pinecone_hybrid_query(
                        host,
                        namespace,
                        top_k,
                        alpha,
                        query_dense_vector,
                        query_sparse_vector,
                        include_metadata,
                        metadata_filter,
                    )
                )
            else:
                pinecone_response = await self.pinecone_service.pinecone_query(
                    index_host=host,
                    namespace=namespace,
                    top_k=top_k,
                    vector=query_dense_vector,
                    include_metadata=include_metadata,
                    filter_dict=metadata_filter,
                )
            matches = pinecone_response.get("matches", [])
            final_responses = []
            for match in matches:
                score = match.get("score", None)
                id = match.get("id", None)
                content = match.get("metadata", None).get("content", None)
                metadata = {
                    key: value
                    for key, value in match.get("metadata").items()
                    if key != "content"
                }
                final_responses.append(
                    {
                        "id": id,
                        "score": score,
                        "content": content,
                        "metadata": metadata,
                    }
                )
            return final_responses

        except Exception as e:
            loggers["main"].error(f"Error in random_query_usecase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
