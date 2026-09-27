from datetime import datetime

from pydantic import BaseModel


class WeatherResponse(BaseModel):
    location_id: int
    temperature: float | None = None
    humidity: float | None = None
    rainfall_mm: float | None = None
    rainfall_intensity: float | None = None
    recorded_at: datetime