import asyncio
import base64
import json
from typing import Dict, List, Optional

from fastapi import Depends

from system.src.app.models.schemas.generate_drafts_schemas import (
    AttachmentSchema,
)
from system.src.app.prompts.generate_drafts_prompts import (
    GENERATE_DRAFTS_SYSTEM_PROMPT,
)
from system.src.app.repositories.error_repository import ErrorRepo
from system.src.app.services.gemini_service import GeminiService
from system.src.app.usecases.generate_drafts_usecases.generate_drafts_usecases_helper import (
    GenerateDraftsHelper,
)
from system.src.app.utils.response_parser import parse_response
from system.src.app.utils.logging_utils import loggers

class GenerateDraftsUsecase:
    def __init__(
        self,
        gemini_service: GeminiService = Depends(GeminiService),
        helper: GenerateDraftsHelper = Depends(GenerateDraftsHelper),
        error_repo: ErrorRepo = Depends(ErrorRepo),
    ):
        self.gemini_service = gemini_service
        self.helper = helper
        self.error_repo = error_repo

    async def generate_drafts(self, query: Dict) -> Dict:
        try:

            # Extract data from query
            sender = query.get("from", "")
            subject = query.get("subject", "")
            body = query.get("body", "")
            rocket_docs_response = query.get("rocket_docs_response", [])
            dataset_response = query.get("dataset_response", [])
            attachments = query.get("attachments", [])
            categories = query.get("categories", [])

            rocket_docs_response, dataset_response = (
                await self.helper.format_pinecone_results(
                    rocket_docs_response, dataset_response
                )
            )

            # Prepare user prompt with formatted data
            user_prompt = self.helper.format_user_prompt(
                sender=sender,
                subject=subject,
                body=body,
                rocket_doc_results=rocket_docs_response,
                dataset_search_results=dataset_response,
                categories=categories,
            )
            with open(
                "intermediate_outputs/8_generate_drafts_user_prompt.txt", "w"
            ) as f:
                f.write(user_prompt)

            # Handle image attachments if present
            images = None
            if attachments:
                processed_images = self._process_attachments(attachments)
                if processed_images:
                    images = processed_images

            # Get system prompt
            system_prompt = GENERATE_DRAFTS_SYSTEM_PROMPT

            # Prepare call parameters - only include images if they exist
            call_params = {
                "user_prompt": user_prompt,
                "system_prompt": system_prompt,
                "temperature": 0.1,
                "top_p": 0.9,
                "top_k": 40,
            }

            # Only add images parameter if there are actual images
            if images is not None and len(images) > 0:
                call_params["images"] = images

            # Check if categories is empty to determine drafts generation strategy
            if categories and len(categories) > 0 and len(dataset_response) > 4:
                # Categories exist - generate single draft
                gemini_response = await self.gemini_service.generate_response(
                    **call_params
                )
                gemini_response = parse_response(gemini_response)
                drafts = gemini_response.get("body", "")
                drafts = [drafts]
            else:
                # Categories empty - generate two drafts in parallel
                draft_task_1 = asyncio.create_task(
                    self.gemini_service.generate_response(**call_params)
                )
                draft_task_2 = asyncio.create_task(
                    self.gemini_service.generate_response(**call_params)
                )

                # Execute both tasks in parallel
                response_1, response_2 = await asyncio.gather(
                    draft_task_1, draft_task_2
                )
                response_1 = parse_response(response_1)
                response_2 = parse_response(response_2)
                # Combine drafts from both responses
                drafts_1 = response_1.get("body", "")
                drafts_2 = response_2.get("body", "")
                drafts = [drafts_1, drafts_2]

            with open(
                "intermediate_outputs/9_generate_drafts_llm_response.json", "w"
            ) as f:
                json.dump(drafts, f)

            final_response = {
                "from": query.get("from", ""),
                "subject": query.get("subject", ""),
                "body": query.get("body", ""),
                "drafts": drafts,
            }

            return final_response

        except Exception as e:
            error_msg = f"Error generating drafts: {str(e)}"
            await self.error_repo.log_error(
                error=error_msg,
                additional_context={
                    "file": "generate_drafts_usecase.py",
                    "method": "generate_drafts",
                    "operation": "generate_drafts",
                    "response_text": error_msg,
                    "sender": query.get("from", ""),
                    "subject": query.get("subject", ""),
                    "categories": query.get("categories", []),
                },
            )
            # Return error response in expected format
            return {
                "from": query.get("from", ""),
                "subject": query.get("subject", ""),
                "body": query.get("body", ""),
                "drafts": [],
                "error": error_msg,
            }

    def _process_attachments(self, attachments: List) -> Optional[List[Dict]]:
        """
        Process attachments and prepare images for Gemini API in the format expected by generate_response.

        :param attachments: List of attachment data
        :return: List of processed images for Gemini in inline_data format or None
        """
        try:
            # Convert attachment data to AttachmentSchema objects
            attachment_objects = []
            for attachment_data in attachments:
                if isinstance(attachment_data, dict):
                    # Create AttachmentSchema object from dict
                    attachment_obj = AttachmentSchema(**attachment_data)
                    attachment_objects.append(attachment_obj)
                else:
                    # Assume it's already an AttachmentSchema object
                    attachment_objects.append(attachment_data)

            # Prepare images for Gemini in the new format
            images = []
            for attachment in attachment_objects:
                # Skip non-image attachments
                if not attachment.is_image:
                    continue

                # Extract base64 data and mime type
                base64_data = attachment.base64_data
                mime_type = attachment.mime_type
                filename = attachment.filename

                # Skip if no base64 data or mime type
                if not base64_data or not mime_type:
                    print(
                        f"Warning: Skipping image '{filename}' - missing base64_data or mime_type"
                    )
                    continue

                # Validate base64 data and format for generate_response
                try:
                    # Test if data can be decoded
                    base64.b64decode(base64_data)
                    image_part = {
                        # "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_data,
                        # }
                    }
                    images.append(image_part)
                    print(
                        f"Successfully processed image: {filename} ({mime_type})"
                    )
                except Exception as e:
                    # Log the error but continue processing other images
                    loggers["main"].error(
                        f"Warning: Failed to process image attachment '{filename}': {str(e)}"
                    )
                    continue

            return images if images else None

        except Exception as e:
            loggers["main"].error(f"Warning: Failed to process attachments: {str(e)}")
            return None
