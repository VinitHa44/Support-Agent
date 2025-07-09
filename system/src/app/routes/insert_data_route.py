import time

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse

from system.src.app.controllers.insert_data_controller import (
    InsertDataController,
)
from system.src.app.utils.error_handler import handle_exceptions

router = APIRouter()


@router.post("/insert-data", status_code=status.HTTP_201_CREATED)
@handle_exceptions
async def create_new_thread(
    file: UploadFile = File(...),
    insert_data_controller: InsertDataController = Depends(
        InsertDataController
    ),
):

    start_time = time.time()
    response = await insert_data_controller.insert_data(file)
    end_time = time.time()
    duration = end_time - start_time

    return JSONResponse(
        content={
            "data": response,
            "status_code": status.HTTP_201_CREATED,
            "detail": f"{file.filename} data inserted successfully",
            "processing_time": round(duration, 4),
        },
        status_code=status.HTTP_201_CREATED,
    )
