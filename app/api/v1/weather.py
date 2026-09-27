from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.location import Location
from app.services.weather_service import get_weather_history
from app.services.live_weather_service import get_live_weather


router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)

@router.get("/regions/current")
def get_all_regions_current_weather(
    db: Session = Depends(get_db),
):

    # Get all monitoring locations
    locations = db.query(Location).all()

    if not locations:
        raise HTTPException(
            status_code=404,
            detail="No locations found",
        )

    regions = []

    for location in locations:

        try:

            # Fetch live weather for this location
            weather = get_live_weather(
                location.latitude,
                location.longitude,
            )

            regions.append(
                {
                    "location_id": location.id,
                    "name": location.name,

                    "latitude": location.latitude,
                    "longitude": location.longitude,

                    "temperature": weather["temperature"],
                    "humidity": weather["humidity"],
                    "rainfall_mm": weather["rainfall_mm"],

                    "recorded_at": datetime.fromtimestamp(
                        weather["recorded_at"]
                    ),
                }
            )

        except Exception as e:

            # Don't destroy the whole forecast
            # if one location fails
            regions.append(
                {
                    "location_id": location.id,
                    "name": location.name,
                    "error": str(e),
                }
            )

    return {
        "regions": regions
    }




@router.get("/{location_id}/current")
def get_current_weather_data(
    location_id: int,
    db: Session = Depends(get_db),
):

    # Get the selected location from database
    location = db.query(Location).filter(
        Location.id == location_id
    ).first()

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    try:

        # Get live weather using latitude and longitude
        weather = get_live_weather(
            location.latitude,
            location.longitude,
        )

        return {
            "location_id": location_id,
            "temperature": weather["temperature"],
            "humidity": weather["humidity"],
            "rainfall_mm": weather["rainfall_mm"],
            "recorded_at": datetime.fromtimestamp(
                weather["recorded_at"]
            ),
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not fetch live weather: {str(e)}",
        )




@router.get("/{location_id}/history")


def get_weather_history_data(
    location_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
):

    data = get_weather_history(
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
                "temperature": item.temperature,
                "humidity": item.humidity,
                "rainfall_mm": item.rainfall_mm,
            }
            for item in data
        ],
    }