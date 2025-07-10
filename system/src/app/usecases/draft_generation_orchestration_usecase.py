import asyncio
import logging
import time
from typing import Dict

from fastapi import Depends

from system.src.app.config.settings import settings
from system.src.app.exceptions.websocket_exceptions import WebSocketTimeoutError
from system.src.app.services.websocket_service import (
    WebSocketManager,
    websocket_manager,
)
from system.src.app.usecases.categorisation_usecase.categorisation_usecase import (
    CategorizationUsecase,
)
from system.src.app.usecases.generate_drafts_usecases.generate_drafts_usecase import (
    GenerateDraftsUsecase,
)
from system.src.app.usecases.query_docs_usecases.query_docs_usecase import (
    QueryDocsUsecase,
)
from system.src.app.usecases.request_logging_usecase import RequestLoggingUsecase
from system.src.app.usecases.template_storage_usecase import TemplateStorageUsecase


class DraftGenerationOrchestrationUsecase:
    def __init__(
        self,
        generate_drafts_usecase: GenerateDraftsUsecase = Depends(
            GenerateDraftsUsecase
        ),
        query_docs_usecase: QueryDocsUsecase = Depends(QueryDocsUsecase),
        categorization_usecase: CategorizationUsecase = Depends(
            CategorizationUsecase
        ),
        request_logging_usecase: RequestLoggingUsecase = Depends(
            RequestLoggingUsecase
        ),
        template_storage_usecase: TemplateStorageUsecase = Depends(
            TemplateStorageUsecase
        ),
        websocket_manager: WebSocketManager = Depends(lambda: websocket_manager),
    ):
        self.generate_drafts_usecase = generate_drafts_usecase
        self.query_docs_usecase = query_docs_usecase
        self.categorization_usecase = categorization_usecase
        self.request_logging_usecase = request_logging_usecase
        self.template_storage_usecase = template_storage_usecase
        self.websocket_manager = websocket_manager

    async def execute_draft_generation_workflow(
        self, query: Dict, user_id: str = "default_user"
    ):
        start_time = time.time()
        if "id" not in query:
            query["id"] = f"api_email_{int(time.time())}"

        categorization_response = await self.categorization_usecase.execute(query)
        rocket_docs_query = categorization_response.get("doc_search_query")
        dataset_query = f"Subject: {categorization_response.get('subject')}\n{categorization_response.get('body')}"
        categories = categorization_response.get("categories")

        tasks = []
        if rocket_docs_query and rocket_docs_query.strip():
            tasks.append(
                self.query_docs_usecase.query_docs(
                    rocket_docs_query, settings.ROCKET_DOCS_PINECONE_INDEX_NAME
                )
            )
        else:
            tasks.append(asyncio.sleep(0, result=[]))
            logging.debug("Skipping rocket docs search - empty or missing doc_search_query")

        if categories and len(categories) > 0:
            tasks.append(
                self.query_docs_usecase.query_docs(
                    dataset_query,
                    settings.PINECONE_INDEX_NAME,
                    categories=categories,
                )
            )
        else:
            tasks.append(asyncio.sleep(0, result=[]))
            logging.debug("Skipping dataset search - empty or missing categories")

        (
            rocket_docs_response,
            dataset_response,
        ) = await asyncio.gather(*tasks)

        generate_drafts_query = {
            "from": categorization_response.get("from"),
            "subject": categorization_response.get("subject"),
            "body": categorization_response.get("body"),
            "rocket_docs_response": rocket_docs_response,
            "dataset_response": dataset_response,
            "categories": categories if categories else [],
            "attachments": query.get("attachments", []),
        }
        generated_drafts = await self.generate_drafts_usecase.generate_drafts(
            generate_drafts_query
        )

        final_draft_body = ""
        user_reviewed = False
        is_skip = False

        if len(generated_drafts.get("drafts", [])) > 1:
            logging.debug(
                f"Multiple drafts generated ({len(generated_drafts.get('drafts', []))}), sending to frontend for review..."
            )
            final_response, is_skip = await self._handle_review_process(
                user_id, generated_drafts
            )
            final_draft_body = final_response.get("drafts", [""])[0]
            user_reviewed = True  # This path is only taken if a review happened
        else:
            logging.debug("Single draft generated, returning directly without review")
            final_response = generated_drafts
            final_draft_body = final_response.get("drafts", [""])[0]
            is_skip = False  # Single draft is never considered skipped

        try:
            await self.template_storage_usecase.store_response_template(
                categorization_response, final_draft_body
            )
        except Exception as e:
            logging.warning(f"Failed to store final response template: {e}")

        processing_time = time.time() - start_time
        await self.request_logging_usecase.log_request(
            query,
            categorization_response,
            final_draft_body,
            processing_time,
            user_id,
            rocket_docs_response,
            dataset_response,
            multiple_drafts_generated=len(generated_drafts.get("drafts", [])) > 1,
            user_reviewed=user_reviewed,
        )

        return {"is_skip": is_skip, "body": final_draft_body}

    async def _handle_review_process(self, user_id: str, draft_data: Dict) -> tuple[Dict, bool]:
        try:
            await self.websocket_manager.wait_for_connection(user_id)
            logging.debug(f"Sending drafts to frontend for user {user_id}...")
            await self.websocket_manager.send_message(
                user_id, {"type": "draft_review", "data": draft_data}
            )

            response, status = await self.websocket_manager.wait_for_draft_response(
                user_id
            )

            if status == "success" and response:
                logging.debug("Route execution RESUMED - user review completed")
                
                # Handle the new response format with is_skip field
                is_skip = response.get("is_skip", False)
                if is_skip:
                    logging.debug("User cancelled draft review - using first draft as fallback")
                    first_draft = draft_data.get("drafts", [""])[0]
                    return {**draft_data, "drafts": [first_draft]}, True
                else:
                    final_draft = response.get("body", "")
                    return {**draft_data, "drafts": [final_draft]}, False
            else:
                logging.warning(
                    f"WebSocket error: {status} - falling back to first draft"
                )
                first_draft = draft_data.get("drafts", [""])[0]
                return {**draft_data, "drafts": [first_draft]}, False

        except WebSocketTimeoutError as e:
            logging.error(f"WebSocket error: {e} - falling back to first draft")
            first_draft = draft_data.get("drafts", [""])[0]
            return {**draft_data, "drafts": [first_draft]}, False
        except Exception as e:
            logging.error(f"An unexpected error occurred during draft review: {e}")
            first_draft = draft_data.get("drafts", [""])[0]
            return {**draft_data, "drafts": [first_draft]}, False 