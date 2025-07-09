import re
import base64
from typing import Dict, Any, List, Optional
from fastapi import HTTPException

from system.src.app.prompts.categorization_prompt import (
    CATEGORIZATION_SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    DEFAULT_CATEGORIES,
    DEFAULT_CATEGORY_DESCRIPTIONS,
)


class CategorizationHelper:
    def __init__(self):
        self.categories = DEFAULT_CATEGORIES
        self.category_descriptions = DEFAULT_CATEGORY_DESCRIPTIONS

    def validate_email_data(self, email_data: Dict[str, Any]) -> None:
        """
        Validate that the email data contains required fields.
        
        :param email_data: The email data dictionary to validate
        :raises HTTPException: If required fields are missing
        """
        required_fields = ['id', 'subject', 'body']
        missing_fields = [field for field in required_fields if field not in email_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields in email data: {missing_fields}"
            )
        
        # Validate that subject and body are strings
        if not isinstance(email_data.get('subject'), str):
            raise HTTPException(
                status_code=400,
                detail="Email subject must be a string"
            )
        
        if not isinstance(email_data.get('body'), str):
            raise HTTPException(
                status_code=400,
                detail="Email body must be a string"
            )

    def format_user_prompt(self, subject: str, body: str) -> str:
        """
        Format the user prompt using the subject and body.
        
        :param subject: Email subject
        :param body: Email body
        :return: Formatted user prompt
        """
        return USER_PROMPT_TEMPLATE.format(
            subject=subject.strip(),
            body=body.strip()
        )

    def format_system_prompt(self) -> str:
        """
        Format the system prompt with current categories and descriptions.
        
        :return: Formatted system prompt
        """
        # Format categories list
        categories_list = "\n".join([f"- {category}" for category in self.categories])
        
        # Format category descriptions
        category_descriptions = "\n".join([
            f"- {category}: {description}"
            for category, description in self.category_descriptions.items()
        ])
        
        return CATEGORIZATION_SYSTEM_PROMPT.format(
            categories_list=categories_list,
            category_descriptions=category_descriptions
        )

    def prepare_images_for_gemini(self, attachments: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Prepare image attachments for Gemini API.
        
        :param attachments: List of attachment dictionaries with schema:
            {
                'filename': str,
                'mime_type': str,
                'size': int,
                'attachment_id': str,
                'is_image': bool,
                'is_inline': bool,
                'base64_data': str | None,
                'data_uri': str | None
            }
        :return: List of formatted image dictionaries for Gemini
        """
        images = []
        
        for attachment in attachments:
            # Skip non-image attachments
            if not attachment.get('is_image', False):
                continue
            
            # Extract base64 data and mime type
            base64_data = attachment.get('base64_data')
            mime_type = attachment.get('mime_type')
            filename = attachment.get('filename', 'unknown')
            
            # Skip if no base64 data or mime type
            if not base64_data or not mime_type:
                print(f"Warning: Skipping image '{filename}' - missing base64_data or mime_type")
                continue
            
            # Validate base64 data
            try:
                # Test if data can be decoded
                base64.b64decode(base64_data)
                images.append({
                    'data': base64_data,
                    'mime_type': mime_type
                })
                print(f"Successfully processed image: {filename} ({mime_type})")
            except Exception as e:
                # Log the error but continue processing other images
                print(f"Warning: Failed to process image attachment '{filename}': {str(e)}")
                continue
        
        return images

    def validate_and_process_result(
        self, 
        categorization_result: Dict[str, Any], 
        email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and process the categorization result from Gemini.
        
        :param categorization_result: Raw result from Gemini API
        :param email_data: Original email data
        :return: Processed and validated result
        """
        try:
            # Validate required fields in the result
            required_fields = ['category', 'query_for_search', 'new_category_name', 'new_category_description']
            for field in required_fields:
                if field not in categorization_result:
                    raise ValueError(f"Missing required field in categorization result: {field}")
            
            # Validate category is a list
            categories = categorization_result['category']
            if not isinstance(categories, list):
                raise ValueError("Category must be a list")
            
            # Validate categories against known categories
            valid_categories = []
            for category in categories:
                if category in self.categories or category == "UNKNOWN":
                    valid_categories.append(category)
                else:
                    print(f"Warning: Unknown category '{category}' found in result, skipping")
            
            if not valid_categories:
                # Fallback to UNKNOWN if no valid categories found
                valid_categories = ["UNKNOWN"]
            
            # Validate new category fields if UNKNOWN is present
            if "UNKNOWN" in valid_categories:
                if not categorization_result.get('new_category_name'):
                    categorization_result['new_category_name'] = "uncategorized_query"
                if not categorization_result.get('new_category_description'):
                    categorization_result['new_category_description'] = "Query that doesn't fit existing categories"
            
            # Build the final result
            processed_result = {
                'email_id': email_data['id'],
                'thread_id': email_data.get('thread_id'),
                'subject': email_data.get('subject', ''),
                'sender': email_data.get('sender', ''),
                'categories': valid_categories,
                'query_for_search': categorization_result.get('query_for_search'),
                'new_category_name': categorization_result.get('new_category_name'),
                'new_category_description': categorization_result.get('new_category_description'),
                'has_images': email_data.get('has_images', False),
                'confidence_indicators': {
                    'multiple_categories': len(valid_categories) > 1,
                    'needs_search': categorization_result.get('query_for_search') is not None,
                    'is_new_category': "UNKNOWN" in valid_categories,
                },
                'processing_metadata': {
                    'processed_attachments': len(email_data.get('attachments', [])),
                    'image_count': len([att for att in email_data.get('attachments', []) if att.get('is_image', False)]),
                }
            }
            
            return processed_result
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing categorization result: {str(e)}"
            )

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

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text by removing potentially harmful content.
        
        :param text: Text to sanitize
        :return: Sanitized text
        """
        if not isinstance(text, str):
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Limit length to prevent extremely long inputs
        max_length = 10000
        if len(text) > max_length:
            text = text[:max_length] + "... [truncated]"
        
        return text
