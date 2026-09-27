from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnvironmentalDataCreate(BaseModel):
    location_id: int

    rainfall_mm: float | None = Field(
        default=None,
        ge=0,
    )

    rainfall_intensity: float | None = Field(
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


class EnvironmentalDataResponse(
    EnvironmentalDataCreate
):
    id: int
    recorded_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )