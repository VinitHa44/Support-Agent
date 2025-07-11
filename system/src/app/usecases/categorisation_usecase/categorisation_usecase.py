import json
import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, status

from system.src.app.repositories.error_repository import ErrorRepo
from system.src.app.services.gemini_service import GeminiService
from system.src.app.usecases.categorisation_usecase.helper import (
    CategorizationHelper,
)
from system.src.app.utils.response_parser import parse_response


class CategorizationUsecase:
    def __init__(
        self,
        gemini_service: GeminiService = Depends(),
        helper: CategorizationHelper = Depends(),
        error_repo: ErrorRepo = Depends(ErrorRepo),
    ) -> None:
        self.gemini_service = gemini_service
        self.helper = helper
        self.error_repo = error_repo

    async def execute(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute email categorization with support for images.

        :param email_data: Dictionary containing email information including:
            - id: message_id
            - thread_id: thread identifier
            - subject: email subject
            - sender: sender email
            - date: email date
            - message_id: message ID header
            - in_reply_to: reply reference
            - body: email body text
            - attachments: list of image attachments in base64 format
            - has_images: boolean indicating if email has images
            - is_unread: boolean
            - internal_date: internal timestamp
            - labels: list of labels
        :return: Dictionary with categorization results
        """
        try:
            os.makedirs("intermediate_outputs", exist_ok=True)
            # Validate required fields
            self.helper.validate_email_data(email_data)

            # Extract key information
            subject = email_data.get("subject", "")
            body = email_data.get("body", "")
            attachments = email_data.get("attachments", [])
            has_images = email_data.get("has_images", False)

            # Prepare user prompt
            user_prompt = self.helper.format_user_prompt(subject, body)

            # Prepare system prompt with dynamic categories
            system_prompt = self.helper.format_system_prompt()

            # Prepare images for Gemini if available
            images = None
            if has_images and attachments:
                images = self.helper.prepare_images_for_gemini(attachments)

            # Call Gemini API for categorization using the updated service
            response_text = await self.gemini_service.generate_response(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                images=images,
                temperature=0.1,  # Low temperature for consistent categorization
            )

            # Parse the JSON response using the response parser utility
            try:
                categorization_result = parse_response(response_text)
                with open(
                    "intermediate_outputs/1_categorization_llm_response.json",
                    "w",
                ) as f:
                    json.dump(categorization_result, f)

                # Ensure we have a valid dict response
                if not isinstance(categorization_result, dict):
                    raise ValueError("Response is not a valid dictionary")

            except Exception as e:
                error_msg = f"Invalid JSON response from Gemini API: {str(e)}. Response: {response_text[:500]}"
                await self.error_repo.log_error(
                    error=error_msg,
                    additional_context={
                        "file": "categorisation_usecase.py",
                        "method": "execute",
                        "operation": "gemini_response_parsing",
                        "response_text": response_text[:500] if response_text else "",
                        "subject": subject,
                        "has_images": has_images,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg,
                )

            # Validate and process the result
            processed_result = self.helper.validate_and_process_result(
                categorization_result, email_data
            )

            with open("intermediate_outputs/2_processed_result.json", "w") as f:
                json.dump(processed_result, f)

            # Return simplified format as requested
            return {
                "categories": processed_result["categories"],
                "new_categories": processed_result["new_categories"],
                "doc_search_query": processed_result["query_for_search"] or "",
                "from": email_data.get("sender", ""),
                "body": email_data.get("body", ""),
                "subject": email_data.get("subject", ""),
            }

        except Exception as e:
            error_msg = f"Error in categorization usecase: {str(e)}"
            await self.error_repo.log_error(
                error=error_msg,
                additional_context={
                    "file": "categorisation_usecase.py",
                    "method": "execute",
                    "operation": "email_categorization",
                    "response_text": error_msg,
                    "email_id": email_data.get("id", ""),
                    "subject": email_data.get("subject", ""),
                    "sender": email_data.get("sender", ""),
                    "has_images": email_data.get("has_images", False),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg,
            )
