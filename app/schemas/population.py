from pydantic import BaseModel, ConfigDict


class PopulationCreate(BaseModel):
    location_id: int
    area_name: str
    population: int
    latitude: float
    longitude: float
    vulnerability_score: float = 0


class PopulationResponse(PopulationCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)