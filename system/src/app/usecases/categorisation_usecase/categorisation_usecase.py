from typing import Any, Dict

from fastapi import Depends, HTTPException

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
    ) -> None:
        self.gemini_service = gemini_service
        self.helper = helper

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

                # Ensure we have a valid dict response
                if not isinstance(categorization_result, dict):
                    raise ValueError("Response is not a valid dictionary")

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Invalid JSON response from Gemini API: {str(e)}. Response: {response_text[:500]}",
                )

            # Validate and process the result
            processed_result = self.helper.validate_and_process_result(
                categorization_result, email_data
            )

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
            raise HTTPException(
                status_code=500,
                detail=f"Error in categorization usecase: {str(e)}",
            )
