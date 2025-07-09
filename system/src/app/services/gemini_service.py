import time
from datetime import datetime

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
        self.api_service = api_service
        self.base_url = settings.GEMINI_BASE_URL
        self.completion_endpoint = settings.GEMINI_COMPLETION_ENDPOINT
        self.gemini_model = settings.GEMINI_MODEL
        self.gemini_api_key = settings.GOOGLE_API_KEY
        self.llm_usage_repository = llm_usage_repository

    async def completions(
        self,
        user_prompt: str,
        system_prompt: str,
        **params,
    ) -> dict:
        """
        This method sends a POST request to the Gemini API to get completions for the given prompts.
        :param user_prompt: The user prompt to get completions for.
        :param system_prompt: The system prompt to set assistant behavior (default: "You are a helpful assistant").
        :param params: Optional parameters for the API request.
        :return: The completion text from the Gemini API.
        """
        url = f"{self.base_url}{self.gemini_model}:{self.completion_endpoint}?key={self.gemini_api_key}"

        headers = {
            "Content-Type": "application/json",
        }
        print(settings.GOOGLE_API_KEY)
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 17000,
            },
        }
        for key, value in params.items():
            if key in ["topP", "topK", "temperature"]:
                payload["generationConfig"][key] = value
        try:
            start_time = time.perf_counter()

            response = await self.api_service.post(
                url=url, headers=headers, data=payload
            )

            end_time = time.perf_counter()
            duration = end_time - start_time

            usage = response.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount", 0)
            completion_tokens = usage.get("candidatesTokenCount", 0)
            total_tokens = usage.get("totalTokenCount", 0)
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
                "response": response,
            }
            await self.llm_usage_repository.add_llm_usage(llm_usage)

            return response["candidates"][0]["content"]["parts"][0]["text"]

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error while sending a POST request to the Gemini API: {str(e)} \n error from gemini_service in completions()",
            )
