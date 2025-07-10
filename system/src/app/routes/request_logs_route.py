from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from system.src.app.models.schemas.request_log_schema import (
    RequestLogResponseSchema,
    RequestLogStatsSchema,
)
from system.src.app.repositories.request_log_repository import (
    RequestLogRepository,
)

router = APIRouter(prefix="/request-logs", tags=["Request Logs"])


@router.get("/stats", response_model=RequestLogStatsSchema)
async def get_request_stats(
    start_date: Optional[datetime] = Query(
        None, description="Start date for statistics (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date for statistics (ISO format)"
    ),
    request_log_repository: RequestLogRepository = Depends(
        RequestLogRepository
    ),
):
    """
    Get comprehensive request statistics for analytics dashboard

    :param start_date: Optional start date for filtering
    :param end_date: Optional end date for filtering
    :param request_log_repository: Request log repository dependency
    :return: Statistics data
    """
    try:
        stats = await request_log_repository.get_request_stats(
            start_date, end_date
        )
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching request statistics: {str(e)}",
        )


@router.get("/user/{user_id}", response_model=List[RequestLogResponseSchema])
async def get_user_request_logs(
    user_id: str,
    limit: int = Query(100, description="Maximum number of logs to return"),
    request_log_repository: RequestLogRepository = Depends(
        RequestLogRepository
    ),
):
    """
    Get request logs for a specific user

    :param user_id: User identifier
    :param limit: Maximum number of logs to return
    :param request_log_repository: Request log repository dependency
    :return: List of request logs
    """
    try:
        logs = await request_log_repository.get_request_logs_by_user(
            user_id, limit
        )
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching user request logs: {str(e)}",
        )


@router.get("/{log_id}", response_model=RequestLogResponseSchema)
async def get_request_log(
    log_id: str,
    request_log_repository: RequestLogRepository = Depends(
        RequestLogRepository
    ),
):
    """
    Get a specific request log by ID

    :param log_id: Request log identifier
    :param request_log_repository: Request log repository dependency
    :return: Request log data
    """
    try:
        log = await request_log_repository.get_request_log_by_id(log_id)
        if not log:
            raise HTTPException(status_code=404, detail="Request log not found")
        return log
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching request log: {str(e)}"
        )
