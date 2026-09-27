from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
 
from app.core.database import get_db
from app.models.location import Location
from app.models.population import Population
 
 
router = APIRouter(
    prefix="/population",
    tags=["Population"],
)
 
 
# NOTE: app/schemas/population.py does not match the `population`
# DB table (it has area_name/population/latitude/longitude, none of
# which exist as columns). This router works directly against the
# real columns: location_id, population_count, vulnerable_population,
# risk_score.
class PopulationCreateIn(BaseModel):
    location_id: int
    population_count: int
    vulnerable_population: int
    risk_score: float = 0.0
 
 
def serialize_population(pop: Population) -> dict:
    return {
        "id": pop.id,
        "location_id": pop.location_id,
        "population_count": pop.population_count,
        "vulnerable_population": pop.vulnerable_population,
        "risk_score": pop.risk_score,
    }
 
 
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_population(
    data: PopulationCreateIn,
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
 
    pop = Population(
        location_id=data.location_id,
        population_count=data.population_count,
        vulnerable_population=data.vulnerable_population,
        risk_score=data.risk_score,
    )
 
    db.add(pop)
    db.commit()
    db.refresh(pop)
 
    return serialize_population(pop)
 
 
@router.get("/")
def get_population(
    location_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Population)
 
    if location_id is not None:
        query = query.filter(Population.location_id == location_id)
 
    return [serialize_population(p) for p in query.all()]
 
 
@router.get("/{population_id}")
def get_population_by_id(
    population_id: int,
    db: Session = Depends(get_db),
):
    pop = db.query(Population).filter(
        Population.id == population_id
    ).first()
 
    if pop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Population record not found",
        )
 
    return serialize_population(pop)
 