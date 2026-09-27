from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.location import Location
from app.services.environmental_data_service import (
    get_environmental_history,
)
from app.services.live_soil_service import (
    get_live_soil_moisture,
)


router = APIRouter(
    prefix="/soil-moisture",
    tags=["Soil Moisture"],
)


@router.get("/{location_id}/current")
def get_current_soil_moisture(
    location_id: int,
    db: Session = Depends(get_db),
):

    # Find the selected location
    location = (
        db.query(Location)
        .filter(Location.id == location_id)
        .first()
    )

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    try:

        # Fetch live soil moisture using location coordinates
        soil = get_live_soil_moisture(
            location.latitude,
            location.longitude,
        )

        return {
            "location_id": location_id,
            "soil_moisture": soil["soil_moisture"],
            "recorded_at": soil["recorded_at"],
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not fetch live soil moisture: {str(e)}",
        )


@router.get("/{location_id}/history")
def get_soil_moisture_history(
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
                "soil_moisture": item.soil_moisture,
            }
            for item in data
        ],
    }