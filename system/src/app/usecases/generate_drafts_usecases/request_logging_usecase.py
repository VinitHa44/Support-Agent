import time
from typing import Dict

from fastapi import Depends

from system.src.app.repositories.error_repository import ErrorRepo
from system.src.app.repositories.request_log_repository import (
    RequestLogRepository,
)
from system.src.app.utils.logging_utils import loggers

class RequestLoggingUsecase:
    def __init__(
        self,
        request_log_repository: RequestLogRepository = Depends(
            RequestLogRepository
        ),
        error_repo: ErrorRepo = Depends(ErrorRepo),
    ):
        self.request_log_repository = request_log_repository
        self.error_repo = error_repo

    async def log_request(
        self,
        query: Dict,
        categorization_response: Dict,
        final_draft: str,
        processing_time: float,
        user_id: str,
        rocket_docs_response: list,
        dataset_response: list,
        multiple_drafts_generated: bool = False,
        user_reviewed: bool = False,
    ):
        """
        Log request data for statistics

        :param query: Original email query
        :param categorization_response: Categorization results
        :param final_draft: Final draft response
        :param processing_time: Time taken to process request
        :param user_id: User identifier
        :param rocket_docs_response: Pinecone search results from rocket docs
        :param dataset_response: Pinecone search results from dataset
        :param multiple_drafts_generated: Whether multiple drafts were generated
        :param user_reviewed: Whether user reviewed the drafts
        """
        try:
            # Combine categories and new_categories
            categories = categorization_response.get("categories", [])
            new_categories = categorization_response.get("new_categories", [])
            combined_categories = categories + new_categories

            # Determine flags
            has_attachments = bool(query.get("attachments", []))
            has_new_categories = bool(new_categories)
            required_docs = bool(
                categorization_response.get("doc_search_query", "").strip()
            )

            # Process Pinecone results for logging
            rocket_docs_count = (
                len(rocket_docs_response) if rocket_docs_response else 0
            )
            dataset_count = len(dataset_response) if dataset_response else 0

            # Extract relevant metadata from Pinecone results
            rocket_docs_metadata = []
            if rocket_docs_response:
                for doc in rocket_docs_response[
                    :5
                ]:  # Store top 5 results metadata
                    if isinstance(doc, dict):
                        rocket_docs_metadata.append(
                            {
                                "relevance_score": doc.get("relevance_score", 0),
                                "metadata": doc.get("metadata", {}),
                            }
                        )

            dataset_metadata = []
            if dataset_response:
                for doc in dataset_response[:5]:  # Store top 5 results metadata
                    if isinstance(doc, dict):
                        dataset_metadata.append(
                            {
                                "relevance_score": doc.get("relevance_score", 0),
                                "metadata": doc.get("metadata", {}),
                            }
                        )

            # Create request log data
            request_log_data = {
                "request_id": query.get("id", f"unknown_{int(time.time())}"),
                "from_email": categorization_response.get("from", ""),
                "subject": categorization_response.get("subject", ""),
                "body": categorization_response.get("body", ""),
                "categories": combined_categories,
                "has_new_categories": has_new_categories,
                "has_attachments": has_attachments,
                "required_docs": required_docs,
                "draft_response": final_draft,
                "processing_time": processing_time,
                "user_id": user_id,
                "categorization_categories": categories,
                "new_categories_created": new_categories,
                "doc_search_query": categorization_response.get(
                    "doc_search_query"
                ),
                "multiple_drafts_generated": multiple_drafts_generated,
                "user_reviewed": user_reviewed,
                # New Pinecone results fields
                "rocket_docs_count": rocket_docs_count,
                "dataset_docs_count": dataset_count,
                "rocket_docs_results": rocket_docs_metadata,
                "dataset_results": dataset_metadata,
                "total_docs_retrieved": rocket_docs_count + dataset_count,
            }

            # Save to database
            await self.request_log_repository.add_request_log(request_log_data)
            print(
                f"Request logged successfully: {request_log_data['request_id']}"
            )
        
        except Exception as e:
            await self.error_repo.log_error(
                error=e,
                additional_context={
                    "file": "request_logging_usecase.py",
                    "method": "log_request",
                    "operation": "request_logging",
                    "request_id": query.get("id", "unknown"),
                    "status_code": 500,
                    "response_text": str(e),
                    "user_id": user_id,
                    "subject": categorization_response.get("subject", ""),
                    "processing_time": processing_time,
                },
            )
            # Log error but don't fail the main process
            loggers["main"].error(f"Warning: Failed to log request: {str(e)}")
