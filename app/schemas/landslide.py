from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LandslideCreate(BaseModel):
    location_id: int
    title: str
    description: str | None = None
    latitude: float
    longitude: float
    severity: str | None = None
    occurred_at: datetime


class LandslideResponse(LandslideCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)