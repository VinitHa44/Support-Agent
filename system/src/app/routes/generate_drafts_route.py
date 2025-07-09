import time

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from system.src.app.controllers.generate_drafts_cnotroller import GenerateDraftsController

from system.src.app.utils.error_handler import handle_exceptions

router = APIRouter()


@router.post("/generate-drafts", status_code=status.HTTP_201_CREATED)
@handle_exceptions
async def create_new_thread(
    generate_drafts_controller: GenerateDraftsController = Depends(GenerateDraftsController),
):

    start_time = time.time()
    response = await generate_drafts_controller.generate_drafts()
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