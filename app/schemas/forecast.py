from datetime import datetime

from pydantic import BaseModel


class RiskPredictionRequest(BaseModel):
    location_id: int


class RiskPredictionResponse(BaseModel):
    location_id: int
    risk_score: float
    risk_level: str
    confidence: float | None = None
    explanation: str | None = None
    model_version: str | None = None
    predicted_at: datetime


class RiskForecastResponse(BaseModel):
    location_id: int
    forecast_time: datetime
    risk_score: float
    risk_level: str
    confidence: float | None = None
    model_version: str | None = None
    created_at: datetime
