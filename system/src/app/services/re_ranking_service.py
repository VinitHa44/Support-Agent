import httpx
from fastapi import Depends, HTTPException, status

from system.src.app.repositories.error_repository import ErrorRepo
from system.src.app.config.settings import settings
from system.src.app.utils.logging_utils import loggers


class RerankerService:
    def __init__(self, error_repo: ErrorRepo = Depends(ErrorRepo)):
        self.voyage_api_key = settings.VOYAGEAI_API_KEY
        self.voyage_base_url = settings.VOYAGEAI_BASE_URL
        self.RERANK_SUFFIX = "rerank"
        self.timeout = httpx.Timeout(
            connect=60.0,  # Time to establish a connection
            read=120.0,  # Time to read the response
            write=120.0,  # Time to send data
            pool=60.0,  # Time to wait for a connection from the pool
        )
        self.error_repo = error_repo
        
    async def voyage_rerank(
        self, model_name: str, query: str, documents: list, top_n: int
    ):
        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {self.voyage_api_key}",
        }

        payload = {
            "model": model_name,
            "query": query,
            "top_k": top_n,
            "documents": documents,
        }

        rerank_url = f"{self.voyage_base_url}/{self.RERANK_SUFFIX}"

        try:
            async with httpx.AsyncClient(
                verify=False, timeout=self.timeout
            ) as client:
                response = await client.post(
                    rerank_url, headers=headers, json=payload
                )
                response.raise_for_status()
                loggers["voyageai"].info(
                    f"Reranking model hosted by Voyage tokens usage : {response.json().get('usage', {})}"
                )
                return response.json()
        except httpx.HTTPStatusError as exc:
            await self.error_repo.log_error(
                error=exc,
                additional_context={
                    "file": "re_ranking_service.py",
                    "method": "voyage_rerank",
                    "url": rerank_url,
                    "status_code": exc.response.status_code,
                    "response_text": (
                        exc.response.text
                        if hasattr(exc.response, "text")
                        else None
                    ),
                    "operation": "voyage_rerank",
                },
            )
            error_msg = f"HTTP error: {exc.response.status_code} - {exc.response.text} - {str(exc)}"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            )
        except httpx.RequestError as exc:
            await self.error_repo.log_error(
                error=exc,
                additional_context={
                    "file": "re_ranking_service.py",
                    "method": "voyage_rerank",
                    "url": rerank_url,
                    "status_code": 502,
                    "response_text": str(exc.request.content),
                    "operation": "voyage_rerank",
                },
            )
            error_msg = f"Failed to connect to API: {str(exc)}"
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_msg,
            )
        except Exception as exc:    
            error_msg = f"Error in voyage rerank: {str(exc)}"
            await self.error_repo.log_error(
                error=error_msg,
                additional_context={
                    "file": "re_ranking_service.py",
                    "method": "voyage_rerank",
                    "url": rerank_url,
                    "operation": "voyage_rerank",
                },
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)