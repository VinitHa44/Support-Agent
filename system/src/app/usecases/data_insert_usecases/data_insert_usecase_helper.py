import hashlib
from typing import Dict, List

from fastapi import Depends, HTTPException

from system.src.app.config.settings import settings
from system.src.app.services.api_service import ApiService
from system.src.app.services.embedding_service import EmbeddingService
from system.src.app.services.pinecone_service import PineconeService
from system.src.app.utils.logging_utils import loggers


class DataInsertUsecaseHelper:
    def __init__(
        self,
        api_service: ApiService = Depends(ApiService),
        embedding_service: EmbeddingService = Depends(EmbeddingService),
        pinecone_service: PineconeService = Depends(PineconeService),
    ):
        self.api_service = api_service
        self.embedding_service = embedding_service
        self.pinecone_service = pinecone_service

    def _generate_vector_id(self, query: str, categories: List[str]) -> str:
        """Generate a unique vector ID based on query and category"""
        category_str = "_".join(categories)
        combined = f"{query}_{category_str}"
        return hashlib.sha256(combined.encode()).hexdigest()

    async def generate_embeddings(self, examples: List[Dict]) -> List[Dict]:
        if not examples:
            loggers["main"].info("No examples to embed")
            return []

        batch_size = settings.EMBEDDINGS_BATCH_SIZE
        all_embeddings = []

        for i in range(0, len(examples), batch_size):
            batch = examples[i : i + batch_size]
            texts = [
                f"Subject: {example['subject']}\n{example['query']}"
                for example in batch
            ]

            try:
                dense_embeddings = (
                    await self.embedding_service.pinecone_dense_embeddings(
                        texts
                    )
                )
                sparse_embeddings = (
                    self.embedding_service.pinecone_sparse_embeddings(texts)
                )

                for j, example in enumerate(batch):
                    embedding_data = {
                        "dense": dense_embeddings[j],
                        "sparse": sparse_embeddings[j],
                        "example": example,  # Include the original example data
                    }
                    all_embeddings.append(embedding_data)

            except Exception as e:
                loggers["main"].error(
                    f"Error generating embeddings for batch: {str(e)}"
                )
                continue

        loggers["main"].info(f"Generated {len(all_embeddings)} embeddings")
        return all_embeddings

    async def upsert_chunks_in_pinecone(self, chunks: List[Dict]) -> Dict:
        if not chunks:
            return {"upserted_count": 0}

        # Ensure index exists before upserting (safety check)
        await self.ensure_pinecone_index_exists()

        vectors_to_upsert = []
        for chunk in chunks:
            example = chunk["example"]  # Get the original example data

            vector_data = {
                "id": self._generate_vector_id(
                    example["query"], example["categories"]
                ),
                "values": chunk["dense"],  # Dense embeddings
                "sparse_values": {
                    "indices": chunk["sparse"]["indices"],
                    "values": chunk["sparse"]["values"],
                },
                "metadata": {
                    "content": example["query"],
                    "response": example["response"],
                    "categories": example["categories"],
                    "from": example["from"],
                    "subject": example["subject"],
                },
            }
            vectors_to_upsert.append(vector_data)

        if vectors_to_upsert:
            result = await self.pinecone_service.upsert_vectors_simplified(
                vectors_to_upsert
            )
            loggers["main"].info(
                f"Upserted {len(vectors_to_upsert)} vectors to Pinecone"
            )

            # Pinecone returns 'upsertedCount', but we need 'upserted_count' for consistency
            upserted_count = result.get("upsertedCount", len(vectors_to_upsert))
            return {"upserted_count": upserted_count}

        return {"upserted_count": 0}

    async def ensure_pinecone_index_exists(self):
        """
        Ensure that the Pinecone index exists. If not, create it.
        This should be called before any Pinecone operations.
        """
        try:
            # First, list all existing indexes
            indexes_response = (
                await self.pinecone_service.list_pinecone_indexes()
            )
            existing_indexes = indexes_response.get("indexes", [])
            index_names = [idx.get("name") for idx in existing_indexes]

            loggers["main"].info(
                f"Found existing Pinecone indexes: {index_names}"
            )

            # Check if our target index exists
            if settings.PINECONE_INDEX_NAME not in index_names:
                loggers["main"].warning(
                    f"Index '{settings.PINECONE_INDEX_NAME}' not found. Creating it..."
                )

                # Create the index with settings from configuration
                await self.pinecone_service.create_index(
                    index_name=settings.PINECONE_INDEX_NAME,
                    dimension=settings.EMBEDDINGS_DIMENSION,
                    metric=settings.INDEXING_SIMILARITY_METRIC,
                )

                loggers["main"].info(
                    f"Successfully created Pinecone index: {settings.PINECONE_INDEX_NAME}"
                )
            else:
                loggers["main"].info(
                    f"Pinecone index '{settings.PINECONE_INDEX_NAME}' already exists"
                )

        except Exception as e:
            loggers["main"].error(
                f"Error ensuring Pinecone index exists: {str(e)}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to ensure Pinecone index exists: {str(e)}",
            )
