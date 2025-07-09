import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException

from system.src.app.config.settings import settings
from system.src.app.repositories.llm_usage_repository import LLMUsageRepository
from system.src.app.services.api_service import ApiService


class GeminiService:
    def __init__(
        self,
        api_service: ApiService = Depends(),
        llm_usage_repository: LLMUsageRepository = Depends(),
    ) -> None:
        self.api_key = settings.GEMINI_API_KEY
        self.url = f"{settings.GEMINI_URL}{self.api_key}"
        self.stream_url = f"{settings.GEMINI_STREAM_URL}{self.api_key}"
        self.api_service = api_service
        self.llm_usage_repository = llm_usage_repository
        self.max_output_tokens = 40000

    async def generate_response(
        self,
        user_prompt: str,
        system_prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
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

            headers = {"Content-Type": "application/json"}

            # Prepare content parts
            parts = []

            # Add images if provided
            if images:
                for image in images:
                    parts.append(
                        {
                            "inline_data": {
                                "mime_type": image.get(
                                    "mime_type", "image/jpeg"
                                ),
                                "data": image.get("data"),
                            }
                        }
                    )

            # Add system prompt and user prompt as text
            combined_prompt = f"{user_prompt}"
            parts.append({"text": combined_prompt})

            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": self.max_output_tokens,
                },
            }

            # Use ApiService for HTTP request
            response_data = await self.api_service.post(
                url=self.url, headers=headers, data=payload
            )

            end_time = time.perf_counter()
            duration = end_time - start_time

            # Extract token usage from response
            usage_metadata = response_data.get("usageMetadata", {})
            prompt_tokens = usage_metadata.get("promptTokenCount", 0)
            completion_tokens = usage_metadata.get("candidatesTokenCount", 0)
            total_tokens = usage_metadata.get(
                "totalTokenCount", prompt_tokens + completion_tokens
            )

            # Track LLM usage
            llm_usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "duration": duration,
                "provider": "Gemini",
                "model": settings.GEMINI_MODEL,
                "created_at": datetime.now().isoformat(),
            }
            await self.llm_usage_repository.add_llm_usage(llm_usage)

            # Extract response text
            try:
                return response_data["candidates"][0]["content"]["parts"][0][
                    "text"
                ]
            except (KeyError, IndexError):
                raise HTTPException(
                    status_code=500,
                    detail="Unexpected response format from Gemini API.",
                )

        except HTTPException:
            # Re-raise HTTPException from ApiService
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing Gemini API request: {str(e)}",
            )
