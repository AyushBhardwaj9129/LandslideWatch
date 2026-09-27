from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.environmental_data_service import (
    get_environmental_history,
    get_latest_environmental_data,
)


router = APIRouter(
    prefix="/rainfall",
    tags=["Rainfall"],
)


@router.get("/{location_id}/current")
def get_current_rainfall(
    location_id: int,
    db: Session = Depends(get_db),
):

    data = get_latest_environmental_data(
        db,
        location_id,
    )

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="No rainfall data found",
        )

    return {
        "location_id": location_id,
        "rainfall_mm": data.rainfall_mm,
        "recorded_at": data.recorded_at,
    }


@router.get("/{location_id}/history")
def get_rainfall_history(
    location_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
):

    data = get_environmental_history(
        db,
        location_id,
        hours,
    )

    return {
        "location_id": location_id,
        "hours": hours,
        "data": [
            {
                "timestamp": item.recorded_at,
                "rainfall_mm": item.rainfall_mm,
            }
            for item in data
        ],
    }