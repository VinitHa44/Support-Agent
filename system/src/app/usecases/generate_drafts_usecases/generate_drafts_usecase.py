from typing import Dict

from fastapi import Depends

from system.src.app.prompts.generate_drafts_prompts import (
    GENERATE_DRAFTS_SYSTEMPROMPT,
    GENERATE_DRAFTS_USER_PROMPT,
)
from system.src.app.services.openai_service import OpenAIService


class GenerateDraftsUsecase:
    def __init__(self, openai_service: OpenAIService = Depends(OpenAIService)):
        self.openai_service = openai_service

    async def generate_drafts(self, query: Dict):
        system_prompt = GENERATE_DRAFTS_SYSTEMPROMPT
        user_prompt = GENERATE_DRAFTS_USER_PROMPT

        response = await self.openai_service.completions(
            system_prompt, user_prompt
        )
        return response
