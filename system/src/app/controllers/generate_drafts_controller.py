from typing import Dict

from fastapi import Depends, HTTPException

from system.src.app.usecases.generate_drafts_usecases.draft_generation_orchestration_usecase import (
    DraftGenerationOrchestrationUsecase,
)


class GenerateDraftsController:
    def __init__(
        self,
        draft_generation_orchestration_usecase: DraftGenerationOrchestrationUsecase = Depends(
            DraftGenerationOrchestrationUsecase
        ),
    ):
        self.draft_generation_orchestration_usecase = (
            draft_generation_orchestration_usecase
        )

    async def generate_drafts(self, query: Dict, user_id: str = "default_user"):
        """
        Generate drafts and handle review process

        :param query: Email query data
        :param user_id: User identifier for WebSocket communication
        :return: Final draft response
        """
        try:
            return await self.draft_generation_orchestration_usecase.execute_draft_generation_workflow(
                query, user_id
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in generate drafts controller: {str(e)}",
            )
