import base64
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException
from google.genai import Client, types

from system.src.app.config.settings import settings
from system.src.app.repositories.llm_usage_repository import LLMUsageRepository


class GeminiService:
    def __init__(
        self,
        llm_usage_repository: LLMUsageRepository = Depends(),
    ) -> None:
        self.client = Client(api_key=settings.GEMINI_API_KEY)
        self.gemini_model = settings.GEMINI_MODEL
        self.llm_usage_repository = llm_usage_repository

    async def completions(
        self,
        user_prompt: str,
        system_prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        **params,
    ) -> str:
        """
        This method sends a request to the Gemini API to get completions for the given prompts.
        Supports multimodal content including images.

        :param user_prompt: The user prompt to get completions for.
        :param system_prompt: The system prompt to set assistant behavior.
        :param images: Optional list of image dictionaries with 'data' (base64) and 'mime_type' keys.
        :param params: Optional parameters for the API request.
        :return: The completion text from the Gemini API.
        """
        try:
            start_time = time.perf_counter()

            # Prepare content parts
            content_parts = [user_prompt]

            # Add images if provided
            if images:
                for image_data in images:
                    if "data" in image_data and "mime_type" in image_data:
                        # Decode base64 image data
                        image_bytes = base64.b64decode(image_data["data"])
                        image_part = types.Part.from_bytes(
                            data=image_bytes, mime_type=image_data["mime_type"]
                        )
                        content_parts.append(image_part)

            # Prepare generation config
            generation_config = {
                "max_output_tokens": 17000,
                "response_mime_type": (
                    "application/json"
                    if params.get("json_output", False)
                    else "text/plain"
                ),
            }

            # Add optional parameters
            for key, value in params.items():
                if key in ["temperature", "top_p", "top_k"]:
                    generation_config[key] = value

            # Generate content
            response = self.client.models.generate_content(
                model=self.gemini_model,
                contents=content_parts,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt, **generation_config
                ),
            )

            end_time = time.perf_counter()
            duration = end_time - start_time

            # Extract usage metadata
            usage = response.usage_metadata
            prompt_tokens = usage.prompt_token_count if usage else 0
            completion_tokens = usage.candidates_token_count if usage else 0
            total_tokens = usage.total_token_count if usage else 0

            # Log usage
            llm_usage = {
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "duration": duration,
                "provider": "Google",
                "model": self.gemini_model,
                "created_at": datetime.utcnow(),
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response": response.text,
            }
            await self.llm_usage_repository.add_llm_usage(llm_usage)

            return response.text

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error while sending a request to the Gemini API: {str(e)} \n error from gemini_service in completions()",
            )

    async def completions_with_json_output(
        self,
        user_prompt: str,
        system_prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        **params,
    ) -> dict:
        """
        This method sends a request to the Gemini API and expects a JSON response.

        :param user_prompt: The user prompt to get completions for.
        :param system_prompt: The system prompt to set assistant behavior.
        :param images: Optional list of image dictionaries with 'data' (base64) and 'mime_type' keys.
        :param params: Optional parameters for the API request.
        :return: The parsed JSON response from the Gemini API.
        """
        try:
            # Set JSON output parameter
            params["json_output"] = True

            response_text = await self.completions(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                images=images,
                **params,
            )

            # Parse JSON response
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                # Try to handle Python-style None values in JSON response
                try:
                    # Replace Python None with JSON null
                    fixed_response = response_text.replace(
                        ": None", ": null"
                    ).replace(":None", ":null")
                    return json.loads(fixed_response)
                except json.JSONDecodeError:
                    # If still fails, try using ast.literal_eval for Python-like responses
                    try:
                        import ast

                        result = ast.literal_eval(response_text)
                        # Convert Python dict with None to JSON-compatible dict with None -> None
                        return result
                    except (ValueError, SyntaxError):
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to parse JSON response from Gemini API: {str(e)}. Response: {response_text}",
                        )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error while getting JSON response from Gemini API: {str(e)}",
            )
