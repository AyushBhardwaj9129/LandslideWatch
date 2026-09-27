from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SensorCreate(BaseModel):
    sensor_id: str
    location_id: int
    sensor_type: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class SensorReading(BaseModel):
    sensor_id: str

    rainfall_mm: float | None = Field(
        default=None,
        ge=0,
    )

    soil_moisture: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    temperature: float | None = Field(
        default=None,
        ge=-50,
        le=60,
    )

    humidity: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    recorded_at: datetime | None = None


class SensorResponse(SensorCreate):
    id: int
    is_active: bool
    last_seen: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True
    )