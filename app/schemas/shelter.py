from pydantic import BaseModel, ConfigDict


class ShelterCreate(BaseModel):
    name: str
    address: str | None = None
    latitude: float
    longitude: float
    capacity: int | None = None
    contact_number: str | None = None
    is_active: bool = True


class ShelterResponse(ShelterCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
