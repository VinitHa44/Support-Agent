import base64
import json
import os
import re
from typing import Any, Dict, List

from fastapi import HTTPException

from system.src.app.prompts.categorization_prompt import (
    CATEGORIZATION_SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)


class CategorizationHelper:
    def __init__(self):
        self.categories_file_path = "session-data/categories.json"
        self.categories, self.category_descriptions = self._load_categories()

    def _load_categories(self) -> tuple[List[str], Dict[str, str]]:
        """
        Load categories and descriptions from JSON file.

        :return: Tuple of (categories_list, category_descriptions_dict)
        """
        try:
            with open(self.categories_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            categories_dict = data.get("categories", {})
            categories_list = list(categories_dict.keys())

            return categories_list, categories_dict

        except FileNotFoundError:
            print(
                f"Warning: Categories file {self.categories_file_path} not found. Using fallback categories."
            )
            # Fallback categories if file not found
            fallback_categories = [
                "billing_financial_management",
                "ai_performance_quality",
                "platform_stability_technical",
            ]
            fallback_descriptions = {
                "billing_financial_management": "Customer billing and payment issues",
                "ai_performance_quality": "AI model performance and quality issues",
                "platform_stability_technical": "Technical platform stability issues",
            }
            return fallback_categories, fallback_descriptions

        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error parsing categories JSON file: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error loading categories: {str(e)}"
            )

    def _save_categories(self) -> None:
        """
        Save current categories and descriptions to JSON file.
        """
        try:
            data = {"categories": self.category_descriptions}

            # Ensure directory exists
            os.makedirs(
                os.path.dirname(self.categories_file_path), exist_ok=True
            )

            with open(self.categories_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(
                f"Categories updated and saved to {self.categories_file_path}"
            )

        except Exception as e:
            print(f"Warning: Failed to save categories to file: {str(e)}")

    def add_new_category(
        self, category_name: str, category_description: str
    ) -> None:
        """
        Add a new category and save to JSON file.

        :param category_name: Name of the new category
        :param category_description: Description of the new category
        """
        if category_name not in self.categories:
            self.categories.append(category_name)
            self.category_descriptions[category_name] = category_description
            self._save_categories()
            print(f"Added new category: {category_name}")
        else:
            print(f"Category {category_name} already exists, skipping addition")

    def validate_email_data(self, email_data: Dict[str, Any]) -> None:
        """
        Validate that the email data contains required fields.

        :param email_data: The email data dictionary to validate
        :raises HTTPException: If required fields are missing
        """
        required_fields = ["id", "subject", "body"]
        missing_fields = [
            field for field in required_fields if field not in email_data
        ]

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields in email data: {missing_fields}",
            )

        # Validate that subject and body are strings
        if not isinstance(email_data.get("subject"), str):
            raise HTTPException(
                status_code=400, detail="Email subject must be a string"
            )

        if not isinstance(email_data.get("body"), str):
            raise HTTPException(
                status_code=400, detail="Email body must be a string"
            )

    def format_user_prompt(self, subject: str, body: str) -> str:
        """
        Format the user prompt using the subject and body.

        :param subject: Email subject
        :param body: Email body
        :return: Formatted user prompt
        """
        return USER_PROMPT_TEMPLATE.format(
            subject=subject.strip(), body=body.strip()
        )

    def format_system_prompt(self) -> str:
        """
        Format the system prompt with current categories and descriptions.

        :return: Formatted system prompt
        """
        # Format categories list
        categories_list = "\n".join(
            [f"- {category}" for category in self.categories]
        )

        # Format category descriptions
        category_descriptions = "\n".join(
            [
                f"- {category}: {description}"
                for category, description in self.category_descriptions.items()
            ]
        )

        return CATEGORIZATION_SYSTEM_PROMPT.format(
            categories_list=categories_list,
            category_descriptions=category_descriptions,
        )

    def prepare_images_for_gemini(
        self, attachments: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
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
            if not attachment.get("is_image", False):
                continue

            # Extract base64 data and mime type
            base64_data = attachment.get("base64_data")
            mime_type = attachment.get("mime_type")
            filename = attachment.get("filename", "unknown")

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

    def validate_and_process_result(
        self, categorization_result: Dict[str, Any], email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and process the categorization result from Gemini.

        :param categorization_result: Raw result from Gemini API
        :param email_data: Original email data
        :return: Processed and validated result
        """
        try:
            # Validate required fields in the result
            required_fields = [
                "category",
                "query_for_search",
                "new_category_name",
                "new_category_description",
            ]
            for field in required_fields:
                if field not in categorization_result:
                    raise ValueError(
                        f"Missing required field in categorization result: {field}"
                    )

            # Validate category is a list
            categories = categorization_result["category"]
            if not isinstance(categories, list):
                raise ValueError("Category must be a list")

            # Validate categories against known categories
            valid_categories = []
            new_categories = []
            for category in categories:
                if category in self.categories:
                    valid_categories.append(category)
                elif category == "UNKNOWN":
                    # Handle new category creation
                    new_category_name = categorization_result.get("new_category_name")
                    new_category_description = categorization_result.get("new_category_description")

                    if not new_category_name:
                        new_category_name = "uncategorized_query"
                    if not new_category_description:
                        new_category_description = "Query that doesn't fit existing categories"

                    # Add the new category to our system
                    self.add_new_category(new_category_name, new_category_description)
                    
                    # Add to new categories list (just the name)
                    new_categories.append(new_category_name)
                else:
                    print(f"Warning: Unknown category '{category}' found in result, skipping")

            # Build the final result
            processed_result = {
                "email_id": email_data["id"],
                "thread_id": email_data.get("thread_id"),
                "subject": email_data.get("subject", ""),
                "sender": email_data.get("sender", ""),
                "categories": valid_categories,  # Only known categories
                "new_categories": new_categories,  # New categories as separate field
                "query_for_search": categorization_result.get("query_for_search"),
                "new_category_name": categorization_result.get("new_category_name"),
                "new_category_description": categorization_result.get("new_category_description"),
                "has_images": email_data.get("has_images", False),
                "confidence_indicators": {
                    "multiple_categories": len(valid_categories) > 1,
                    "needs_search": categorization_result.get("query_for_search") is not None,
                    "has_new_categories": len(new_categories) > 0,
                },
                "processing_metadata": {
                    "processed_attachments": len(email_data.get("attachments", [])),
                    "image_count": len([
                        att
                        for att in email_data.get("attachments", [])
                        if att.get("is_image", False)
                    ]),
                },
            }

            return processed_result

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing categorization result: {str(e)}",
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
        text = re.sub(r"\s+", " ", text).strip()

        # Limit length to prevent extremely long inputs
        max_length = 10000
        if len(text) > max_length:
            text = text[:max_length] + "... [truncated]"

        return text
