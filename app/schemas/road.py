from pydantic import BaseModel, ConfigDict


class RoadCreate(BaseModel):
    location_id: int | None = None
    name: str
    road_type: str | None = None
    latitude: float
    longitude: float
    vulnerability_score: float = 0
    description: str | None = None


class RoadResponse(RoadCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)