from pydantic import BaseModel, ConfigDict


class LocationCreate(BaseModel):
    name: str
    state: str
    district: str | None = None
    latitude: float
    longitude: float
    elevation: float | None = None


class LocationResponse(LocationCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)