import asyncio
from typing import Dict

from fastapi import Depends, HTTPException

from system.src.app.config.settings import settings
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
    ):
        self.generate_drafts_usecase = generate_drafts_usecase
        self.query_docs_usecase = query_docs_usecase
        self.categorization_usecase = categorization_usecase
        self.data_insert_usecase = data_insert_usecase

    async def generate_drafts(self, query: Dict, user_id: str = "default_user"):
        """
        Generate drafts and handle review process
        
        :param query: Email query data
        :param user_id: User identifier for WebSocket communication
        :return: Final draft response
        """
        try:
            # Add missing 'id' field required by categorization usecase
            if "id" not in query:
                import time
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

                    return {"body": fallback_draft}
            else:
                # Single draft or no drafts - return directly (no review needed)
                print(
                    f"Single draft generated, returning directly without review"
                )
                single_draft = drafts[0] if drafts else "No draft available"

                return {"body": single_draft}

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in generate drafts controller: {str(e)}",
            )
