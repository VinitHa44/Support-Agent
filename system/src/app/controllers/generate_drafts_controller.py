import asyncio
import time
from typing import Dict

from fastapi import Depends, HTTPException

from system.src.app.config.settings import settings
from system.src.app.repositories.request_log_repository import RequestLogRepository
from system.src.app.services.websocket_service import websocket_manager
from system.src.app.usecases.categorisation_usecase.categorisation_usecase import (
    CategorizationUsecase,
)
from system.src.app.usecases.data_insert_usecases.data_insert_usecase import (
    DataInsertUsecase,
)
from system.src.app.usecases.generate_drafts_usecases.generate_drafts_usecase import (
    GenerateDraftsUsecase,
)
from system.src.app.usecases.query_docs_usecases.query_docs_usecase import (
    QueryDocsUsecase,
)


class GenerateDraftsController:
    def __init__(
        self,
        generate_drafts_usecase: GenerateDraftsUsecase = Depends(
            GenerateDraftsUsecase
        ),
        query_docs_usecase: QueryDocsUsecase = Depends(QueryDocsUsecase),
        categorization_usecase: CategorizationUsecase = Depends(
            CategorizationUsecase
        ),
        data_insert_usecase: DataInsertUsecase = Depends(DataInsertUsecase),
        request_log_repository: RequestLogRepository = Depends(RequestLogRepository),
    ):
        self.generate_drafts_usecase = generate_drafts_usecase
        self.query_docs_usecase = query_docs_usecase
        self.categorization_usecase = categorization_usecase
        self.data_insert_usecase = data_insert_usecase
        self.request_log_repository = request_log_repository

    async def generate_drafts(self, query: Dict, user_id: str = "default_user"):
        """
        Generate drafts and handle review process
        
        :param query: Email query data
        :param user_id: User identifier for WebSocket communication
        :return: Final draft response
        """
        # Start timing for performance tracking
        start_time = time.time()
        
        try:
            # Add missing 'id' field required by categorization usecase
            if "id" not in query:
                query["id"] = f"api_email_{int(time.time())}"
            
            # Get categorization response
            categorization_response = await self.categorization_usecase.execute(
                query
            )

            rocket_docs_query = categorization_response.get("doc_search_query")
            dataset_query = f"Subject: {categorization_response.get('subject')}\n{categorization_response.get('body')}"
            categories = categorization_response.get("categories")

            # Query documents in parallel
            # Prepare search tasks, but only if the required data is present
            tasks = []

            # Check if rocket_docs_query is present and not empty
            if rocket_docs_query and rocket_docs_query.strip():
                rocket_docs_task = self.query_docs_usecase.query_docs(
                    rocket_docs_query, settings.ROCKET_DOCS_PINECONE_INDEX_NAME
                )
                tasks.append(("rocket_docs", rocket_docs_task))
            else:
                print(
                    "Skipping rocket docs search - empty or missing doc_search_query"
                )

            # Check if categories are present and not empty
            if categories and len(categories) > 0:
                dataset_task = self.query_docs_usecase.query_docs(
                    dataset_query,
                    settings.PINECONE_INDEX_NAME,
                    categories=categories,
                )
                tasks.append(("dataset", dataset_task))
            else:
                print("Skipping dataset search - empty or missing categories")

            # Execute available tasks
            results = {}
            if tasks:
                # Execute only the available tasks
                task_names = [task[0] for task in tasks]
                task_coroutines = [task[1] for task in tasks]
                task_results = await asyncio.gather(*task_coroutines)

                # Map results back to their names
                for name, result in zip(task_names, task_results):
                    results[name] = result

            # Get results or empty lists if tasks were skipped
            rocket_docs_response = results.get("rocket_docs", [])
            dataset_response = results.get("dataset", [])

            generate_drafts_query = {
                "from": categorization_response.get("from"),
                "subject": categorization_response.get("subject"),
                "body": categorization_response.get("body"),
                "rocket_docs_response": rocket_docs_response,
                "dataset_response": dataset_response,
                "categories": categories if categories else [],  # Ensure categories is always a list
                # "categories": [],
                "attachments": query.get(
                    "attachments", []
                ),  # Pass attachments from original query
            }
            generate_drafts_response = (
                await self.generate_drafts_usecase.generate_drafts(
                    generate_drafts_query
                )
            )
            # Check if drafts length > 1 for review process
            drafts = generate_drafts_response.get("drafts", [])

            if len(drafts) > 1:
                print(
                    f"Multiple drafts generated ({len(drafts)}), sending to frontend for review..."
                )
                print(
                    f"Route execution PAUSED - waiting for user review via WebSocket..."
                )

                # Send drafts to frontend for review via WebSocket
                # THIS PAUSES ROUTE EXECUTION until user responds
                try:
                    final_response = (
                        await websocket_manager.send_draft_for_review(
                            user_id, generate_drafts_response
                        )
                    )

                    print(f"Route execution RESUMED - user review completed")
                    print(
                        f"Final user choice received, returning to calling service"
                    )

                    # Store the final response as a template before returning
                    try:
                        # Combine categories and new_categories
                        categories = categorization_response.get(
                            "categories", []
                        )
                        new_categories = categorization_response.get(
                            "new_categories", []
                        )
                        combined_categories = categories + new_categories

                        # Create the template in the required format
                        template_data = [
                            {
                                "subject": categorization_response.get(
                                    "subject", ""
                                ),
                                "from": categorization_response.get("from", ""),
                                "query": categorization_response.get(
                                    "body", ""
                                ),
                                "response": final_response.get("body", ""),
                                "categories": combined_categories,
                            }
                        ]

                        # Call data insert usecase to store the template
                        result = await self.data_insert_usecase.execute(
                            new_template=template_data
                        )
                        print(
                            f"Successfully stored final response template: {result}"
                        )

                    except Exception as e:
                        # Log the error but don't fail the main process
                        print(
                            f"Warning: Failed to store final response template: {str(e)}"
                        )

                    # Log the request before returning
                    processing_time = time.time() - start_time
                    await self._log_request(
                        query, 
                        categorization_response, 
                        final_response.get("body", ""),
                        processing_time,
                        user_id,
                        rocket_docs_response,
                        dataset_response,
                        multiple_drafts_generated=True,
                        user_reviewed=True
                    )

                    # Return the final user-selected draft to the calling service (e.g., Gmail)
                    return {"body": final_response.get("body", "")}

                except Exception as e:
                    # If WebSocket fails, return the first draft as fallback
                    print(
                        f"WebSocket error: {str(e)} - falling back to first draft"
                    )
                    fallback_draft = (
                        drafts[0] if drafts else "No draft available"
                    )

                    # Store the fallback response as a template before returning
                    try:
                        # Combine categories and new_categories
                        categories = categorization_response.get(
                            "categories", []
                        )
                        new_categories = categorization_response.get(
                            "new_categories", []
                        )
                        combined_categories = categories + new_categories

                        # Create the template in the required format
                        template_data = [
                            {
                                "subject": categorization_response.get(
                                    "subject", ""
                                ),
                                "from": categorization_response.get("from", ""),
                                "query": categorization_response.get(
                                    "body", ""
                                ),
                                "response": fallback_draft,
                                "categories": combined_categories,
                            }
                        ]

                        # Call data insert usecase to store the template
                        result = await self.data_insert_usecase.execute(
                            new_template=template_data
                        )
                        print(
                            f"Successfully stored fallback response template: {result}"
                        )

                    except Exception as e:
                        # Log the error but don't fail the main process
                        print(
                            f"Warning: Failed to store fallback response template: {str(e)}"
                        )

                    # Log the request before returning
                    processing_time = time.time() - start_time
                    await self._log_request(
                        query, 
                        categorization_response, 
                        fallback_draft,
                        processing_time,
                        user_id,
                        rocket_docs_response,
                        dataset_response,
                        multiple_drafts_generated=True,
                        user_reviewed=False
                    )

                    return {"body": fallback_draft}
            else:
                # Single draft or no drafts - return directly (no review needed)
                print(
                    f"Single draft generated, returning directly without review"
                )
                single_draft = drafts[0] if drafts else "No draft available"

                # Log the request before returning
                processing_time = time.time() - start_time
                await self._log_request(
                    query, 
                    categorization_response, 
                    single_draft,
                    processing_time,
                    user_id,
                    rocket_docs_response,
                    dataset_response,
                    multiple_drafts_generated=False,
                    user_reviewed=False
                )

                return {"body": single_draft}

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in generate drafts controller: {str(e)}",
            )

    async def _log_request(
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
            required_docs = bool(categorization_response.get("doc_search_query", "").strip())
            
            # Process Pinecone results for logging
            rocket_docs_count = len(rocket_docs_response) if rocket_docs_response else 0
            dataset_count = len(dataset_response) if dataset_response else 0
            
            # Extract relevant metadata from Pinecone results
            rocket_docs_metadata = []
            if rocket_docs_response:
                for doc in rocket_docs_response[:5]:  # Store top 5 results metadata
                    if isinstance(doc, dict):
                        rocket_docs_metadata.append({
                            "score": doc.get("score", 0),
                            "id": doc.get("id", ""),
                            "metadata": doc.get("metadata", {})
                        })
            
            dataset_metadata = []
            if dataset_response:
                for doc in dataset_response[:5]:  # Store top 5 results metadata
                    if isinstance(doc, dict):
                        dataset_metadata.append({
                            "score": doc.get("score", 0),
                            "id": doc.get("id", ""),
                            "metadata": doc.get("metadata", {})
                        })
            
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
                "doc_search_query": categorization_response.get("doc_search_query"),
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
            print(f"Request logged successfully: {request_log_data['request_id']}")
            print(f"  - Rocket docs retrieved: {rocket_docs_count}")
            print(f"  - Dataset docs retrieved: {dataset_count}")
            print(f"  - Total docs retrieved: {rocket_docs_count + dataset_count}")
            
        except Exception as e:
            # Log error but don't fail the main process
            print(f"Warning: Failed to log request: {str(e)}")
