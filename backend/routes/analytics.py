from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from dependencies import get_current_user
from services.analytics import VALID_PERIODS, build_analytics_response

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
async def get_analytics(
    current_user: dict = Depends(get_current_user),
    period: Optional[str] = Query("week", description="day, week, or month"),
):
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail="Invalid period. Must be day, week, or month.",
        )
    uid = str(current_user["_id"])
    return await build_analytics_response(uid, period)