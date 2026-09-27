from app.models.location import Location
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.location import Location
from app.schemas.location import (
    LocationCreate,
    LocationResponse,
)


router = APIRouter(
    prefix="/locations",
    tags=["Locations"],
)


@router.post(
    "/",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db),
):

    location = Location(
        name=location_data.name,
        state=location_data.state,
        district=location_data.district,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        elevation=location_data.elevation,
    )

    db.add(location)
    db.commit()
    db.refresh(location)

    return location


@router.get(
    "/",
    response_model=list[LocationResponse],
)
@router.get(
    "/",
    response_model=list[LocationResponse],
)
def get_locations(
    state: str | None = Query(
        default=None,
        description="Filter locations by state",
    ),
    district: str | None = Query(
        default=None,
        description="Filter locations by district",
    ),
    db: Session = Depends(get_db),
):

    query = db.query(Location)

    if state:
        query = query.filter(
            Location.state.ilike(state)
        )

    if district:
        query = query.filter(
            Location.district.ilike(district)
        )

    return query.all()


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
)
def get_location(
    location_id: int,
    db: Session = Depends(get_db),
):

    location = db.query(Location).filter(
        Location.id == location_id
    ).first()

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

    return location


@router.put(
    "/{location_id}",
    response_model=LocationResponse,
)
def update_location(
    location_id: int,
    location_data: LocationCreate,
    db: Session = Depends(get_db),
):

    location = db.query(Location).filter(
        Location.id == location_id
    ).first()

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

    location.name = location_data.name
    location.state = location_data.state
    location.district = location_data.district
    location.latitude = location_data.latitude
    location.longitude = location_data.longitude
    location.elevation = location_data.elevation

    db.commit()
    db.refresh(location)

    return location
@router.delete(
    "/{location_id}",
)
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
):

    location = db.query(Location).filter(
        Location.id == location_id
    ).first()

    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )

    db.delete(location)
    db.commit()

    return {
        "message": "Location deleted successfully"
    }