from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
 
from app.core.database import get_db
from app.models.shelter import Shelter
from app.schemas.shelter import ShelterCreate, ShelterResponse
 
 
router = APIRouter(
    prefix="/shelters",
    tags=["Shelters"],
)
 
 
@router.post(
    "/",
    response_model=ShelterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_shelter(
    shelter_data: ShelterCreate,
    db: Session = Depends(get_db),
):
    shelter = Shelter(
        name=shelter_data.name,
        address=shelter_data.address,
        latitude=shelter_data.latitude,
        longitude=shelter_data.longitude,
        capacity=shelter_data.capacity,
        contact_number=shelter_data.contact_number,
        is_active=shelter_data.is_active,
    )
 
    db.add(shelter)
    db.commit()
    db.refresh(shelter)
 
    return shelter
 
 
@router.get(
    "/",
    response_model=list[ShelterResponse],
)
def get_shelters(
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Shelter)
 
    if is_active is not None:
        query = query.filter(Shelter.is_active == is_active)
 
    return query.all()
 
 
@router.get(
    "/{shelter_id}",
    response_model=ShelterResponse,
)
def get_shelter(
    shelter_id: int,
    db: Session = Depends(get_db),
):
    shelter = db.query(Shelter).filter(Shelter.id == shelter_id).first()
 
    if shelter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shelter not found",
        )
 
    return shelter
 
 
@router.put(
    "/{shelter_id}",
    response_model=ShelterResponse,
)
def update_shelter(
    shelter_id: int,
    shelter_data: ShelterCreate,
    db: Session = Depends(get_db),
):
    shelter = db.query(Shelter).filter(Shelter.id == shelter_id).first()
 
    if shelter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shelter not found",
        )
 
    shelter.name = shelter_data.name
    shelter.address = shelter_data.address
    shelter.latitude = shelter_data.latitude
    shelter.longitude = shelter_data.longitude
    shelter.capacity = shelter_data.capacity
    shelter.contact_number = shelter_data.contact_number
    shelter.is_active = shelter_data.is_active
 
    db.commit()
    db.refresh(shelter)
 
    return shelter
 
 
@router.delete("/{shelter_id}")
def delete_shelter(
    shelter_id: int,
    db: Session = Depends(get_db),
):
    shelter = db.query(Shelter).filter(Shelter.id == shelter_id).first()
 
    if shelter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shelter not found",
        )
 
    db.delete(shelter)
    db.commit()
 
    return {"message": "Shelter deleted successfully"}
 