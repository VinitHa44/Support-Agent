import time

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi.responses import JSONResponse

from system.src.app.controllers.generate_drafts_controller import (
    GenerateDraftsController,
)
from system.src.app.models.schemas import GenerateDraftsRequestSchema
from system.src.app.utils.error_handler import handle_exceptions

router = APIRouter()


@router.post("/generate-drafts", status_code=status.HTTP_201_CREATED)
@handle_exceptions
async def create_new_thread(
    generate_drafts_controller: GenerateDraftsController = Depends(
        GenerateDraftsController
    ),
    query: GenerateDraftsRequestSchema = Body(...),
    user_id: str = Query(
        default="default_user",
        description="User ID for WebSocket communication",
    ),
):
    """
    Generate drafts for customer support emails

    :param generate_drafts_controller: Controller instance
    :param query: Email query data
    :param user_id: User identifier for WebSocket communication
    :return: Draft response
    """
    start_time = time.time()
    query_dict = query.model_dump()
    response = await generate_drafts_controller.generate_drafts(
        query_dict, user_id
    )
    end_time = time.time()
    duration = end_time - start_time

    return JSONResponse(
        content={
            "data": response,
            "status_code": status.HTTP_201_CREATED,
            "detail": "Drafts generated successfully",
            "processing_time": round(duration, 4),
        },
        status_code=status.HTTP_201_CREATED,
    )
