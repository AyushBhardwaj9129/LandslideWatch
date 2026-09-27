from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.location import Location
from app.schemas.environmental_data import (
    EnvironmentalDataCreate,
    EnvironmentalDataResponse,
)
from app.services.environmental_data_service import (
    create_environmental_data,
    get_environmental_history,
    get_latest_environmental_data,
)


router = APIRouter(
    prefix="/environmental-data",
    tags=["Environmental Data"],
)


@router.post(
    "/",
    response_model=EnvironmentalDataResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_data(
    data: EnvironmentalDataCreate,
    db: Session = Depends(get_db),
):

    location = db.query(Location).filter(
        Location.id == data.location_id
    ).first()

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

    return create_environmental_data(
        db=db,
        location_id=data.location_id,
        rainfall_mm=data.rainfall_mm,
        rainfall_intensity=data.rainfall_intensity,
        soil_moisture=data.soil_moisture,
        temperature=data.temperature,
        humidity=data.humidity,
    )


@router.get(
    "/{location_id}/latest",
    response_model=EnvironmentalDataResponse,
)
def get_latest_data(
    location_id: int,
    db: Session = Depends(get_db),
):

    data = get_latest_environmental_data(
        db,
        location_id,
    )

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No environmental data found",
        )

    return data


@router.get(
    "/{location_id}/history",
    response_model=list[EnvironmentalDataResponse],
)
def get_history(
    location_id: int,
    hours: int = Query(
        default=24,
        ge=1,
        le=720,
        description="Number of hours of historical data",
    ),
    db: Session = Depends(get_db),
):

    return get_environmental_history(
        db,
        location_id,
        hours,
    )