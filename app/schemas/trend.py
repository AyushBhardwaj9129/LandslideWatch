from datetime import datetime

from pydantic import BaseModel


class TrendDataPoint(BaseModel):
    timestamp: datetime
    value: float


class EnvironmentalTrendResponse(BaseModel):
    location_id: int
    metric: str
    data: list[TrendDataPoint]