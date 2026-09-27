from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
 
from app.core.database import get_db
from app.models.location import Location
from app.models.road import Road
 
 
router = APIRouter(
    prefix="/roads",
    tags=["Roads"],
)
 
 
def risk_level_from_score(score: float) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 35:
        return "MODERATE"
    return "LOW"
 
 
# NOTE: app/schemas/road.py does not match the `roads` DB table
# (it has road_type/vulnerability_score/description, none of which
# exist as columns). This router works directly against the real
# columns: name, location_id, latitude, longitude, risk_score,
# risk_level, is_blocked.
class RoadCreateIn(BaseModel):
    name: str
    location_id: int
    latitude: float
    longitude: float
    risk_score: float = 0.0
 
 
def serialize_road(road: Road) -> dict:
    return {
        "id": road.id,
        "name": road.name,
        "location_id": road.location_id,
        "latitude": road.latitude,
        "longitude": road.longitude,
        "risk_level": road.risk_level,
        "risk_score": road.risk_score,
        "is_blocked": road.is_blocked,
        "created_at": road.created_at,
    }
 
 
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_road(
    road_data: RoadCreateIn,
    db: Session = Depends(get_db),
):
    location = db.query(Location).filter(
        Location.id == road_data.location_id
    ).first()
 
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
 
    road = Road(
        name=road_data.name,
        location_id=road_data.location_id,
        latitude=road_data.latitude,
        longitude=road_data.longitude,
        risk_score=road_data.risk_score,
        risk_level=risk_level_from_score(road_data.risk_score),
        is_blocked=False,
    )
 
    db.add(road)
    db.commit()
    db.refresh(road)
 
    return serialize_road(road)
 
 
@router.get("/")
def get_roads(
    location_id: int | None = Query(default=None),
    is_blocked: bool | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Road)
 
    if location_id is not None:
        query = query.filter(Road.location_id == location_id)
 
    if is_blocked is not None:
        query = query.filter(Road.is_blocked == is_blocked)
 
    if risk_level is not None:
        query = query.filter(Road.risk_level.ilike(risk_level))
 
    return [serialize_road(r) for r in query.all()]
 
 
@router.get("/{road_id}")
def get_road(
    road_id: int,
    db: Session = Depends(get_db),
):
    road = db.query(Road).filter(Road.id == road_id).first()
 
    if road is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Road not found",
        )
 
    return serialize_road(road)
 
 
@router.patch("/{road_id}/block")
def set_road_blocked(
    road_id: int,
    is_blocked: bool,
    db: Session = Depends(get_db),
):
    road = db.query(Road).filter(Road.id == road_id).first()
 
    if road is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Road not found",
        )
 
    road.is_blocked = is_blocked
 
    db.commit()
    db.refresh(road)
 
    return serialize_road(road)
 