import logging
import pickle

import httpx
from fastapi import HTTPException

from system.src.app.config.settings import settings
from system.src.app.utils.logging_utils import loggers

logger = logging.getLogger(__name__)

with open("bm25_encoder.pkl", "rb") as f:
    bm25 = pickle.load(f)


class EmbeddingService:
    def __init__(self):
        self.pinecone_api_key = settings.PINECONE_API_KEY
        self.dense_embed_url = settings.PINECONE_EMBED_URL
        self.pinecone_embedding_url = settings.PINECONE_EMBED_URL
        self.pinecone_api_version = settings.PINECONE_API_VERSION
        self.timeout = httpx.Timeout(
            connect=60.0,  # Time to establish a connection
            read=300.0,  # Time to read the response
            write=300.0,  # Time to send data
            pool=60.0,  # Time to wait for a connection from the pool
        )

    async def pinecone_dense_embeddings(
        self,
        inputs: list,
        embedding_model: str = "llama-text-embed-v2",
        input_type: str = "passage",
        truncate: str = "END",
        dimension: int = 1024,
    ):
        # Format inputs as objects with 'text' field as expected by Pinecone API
        formatted_inputs = [{"text": text} for text in inputs]

        payload = {
            "model": embedding_model,
            "parameters": {
                "input_type": input_type,
                "truncate": truncate,
                # "dimension": dimension,
            },
            "inputs": formatted_inputs,
        }

        if embedding_model != "multilingual-e5-large":
            payload["parameters"]["dimension"] = dimension

        headers = {
            "Api-Key": self.pinecone_api_key,
            "Content-Type": "application/json",
            "X-Pinecone-API-Version": self.pinecone_api_version,
        }

        url = self.dense_embed_url

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                loggers["main"].info("embeddings generated")
                response = response.json()
                loggers["pinecone"].info(
                    f"pinecone hosted embedding model tokens usage: {response['usage']}"
                )
                list_result = [item["values"] for item in response["data"]]
                return list_result

        except httpx.HTTPStatusError as e:
            loggers["main"].error(
                f"Error dense embeddings in pinecone dense embeddings: {e.response.text}"
            )
            raise HTTPException(
                status_code=400, detail=f"{str(e)}-{e.response.text}"
            )
        except Exception as e:
            loggers["main"].error(
                f"Error dense embeddings in pinecone dense embeddings: {str(e)}"
            )
            raise HTTPException(status_code=500, detail=str(e))

    def pinecone_sparse_embeddings(self, inputs):
        try:
            sparse_vector = bm25.encode_documents(inputs)
            return sparse_vector

        except Exception as e:
            loggers["main"].error(f"Error creating sparse embeddings: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
