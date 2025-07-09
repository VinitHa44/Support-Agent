import base64
from typing import Any, Dict, List, Tuple
from system.src.app.prompts.generate_drafts_prompts import GENERATE_DRAFTS_USER_PROMPT

from fastapi import HTTPException

from system.src.app.models.schemas.generate_drafts_schemas import AttachmentSchema


class GenerateDraftsHelper:
    def __init__(self):
        pass

    async def format_rocket_docs_response(self, rocket_docs_response: List[Dict]) -> List[Dict]:
        formatted_rocket_docs_response = []
        if rocket_docs_response:
            for result in rocket_docs_response:
                formatted_rocket_docs_response.append(result.get("query", ""))
        return formatted_rocket_docs_response

    async def format_dataset_response(self, dataset_response: List[Dict]) -> List[Dict]:
        formatted_dataset_response = []
        if dataset_response:
            element = {}
            for result in dataset_response:
                element["query"] = result.get("query", "")
                element["response"] = result.get("metadata", {}).get("response", "")
                element["from"] = result.get("metadata", {}).get("from", "")
                element["subject"] = result.get("metadata", {}).get("subject", "")
                formatted_dataset_response.append(element)
        return formatted_dataset_response

    async def format_pinecone_results(self, rocket_docs_response: List[Dict], dataset_response: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        if rocket_docs_response:
            rocket_docs_response = await self.format_rocket_docs_response(rocket_docs_response)
        if dataset_response:
            dataset_response = await self.format_dataset_response(dataset_response)
        return rocket_docs_response, dataset_response
        

    def format_user_prompt(
        self,
        sender: str,
        subject: str,
        body: str,
        rocket_doc_results: List[Dict],
        dataset_search_results: List[Dict],
    ) -> str:
        # Format rocket docs results
        rocket_docs_formatted = f"ROCKET DOCS:\n"
        for result in rocket_doc_results:
            rocket_docs_formatted += f"{result}\n"

        # Format dataset search results
        dataset_formatted = f"DATASET:\n"
        for result in dataset_search_results:
            dataset_formatted += f"Query: {result.get('query', '')}\nResponse: {result.get('response', '')}\nFrom: {result.get('from', '')}\nSubject: {result.get('subject', '')}\n"

        user_prompt = GENERATE_DRAFTS_USER_PROMPT.format(
            docs_content=rocket_docs_formatted,
            email_content=f"From: {sender}\nSubject: {subject}\nBody: {body}",
            reference_templates=dataset_formatted
        )
        return user_prompt

    def prepare_images_for_gemini(
        self, attachments: List[AttachmentSchema]
    ) -> List[Dict[str, str]]:
        """
        Prepare image attachments for Gemini API using the attachment schema.

        :param attachments: List of AttachmentSchema objects
        :return: List of formatted image dictionaries for Gemini
        """
        images = []

        for attachment in attachments:
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

            # Validate base64 data
            try:
                # Test if data can be decoded
                base64.b64decode(base64_data)
                images.append({"data": base64_data, "mime_type": mime_type})
                print(f"Successfully processed image: {filename} ({mime_type})")
            except Exception as e:
                # Log the error but continue processing other images
                print(
                    f"Warning: Failed to process image attachment '{filename}': {str(e)}"
                )
                continue

        return images

    def _extract_drafts_from_text(self, text_response: str) -> Dict[str, Any]:
        """
        Extract drafts from text response if JSON parsing fails.

        :param text_response: Raw text response from Gemini
        :return: Dictionary with drafts field
        """
        # Simple implementation - treat the entire response as a single draft
        # This can be enhanced based on specific response patterns
        return {
            "drafts": [text_response.strip()]
        }

    def is_valid_base64(self, data: str) -> bool:
        """
        Check if a string is valid base64.

        :param data: String to check
        :return: True if valid base64, False otherwise
        """
        try:
            if isinstance(data, str):
                # Check if it's valid base64
                base64.b64decode(data)
                return True
        except Exception:
            pass
        return False 