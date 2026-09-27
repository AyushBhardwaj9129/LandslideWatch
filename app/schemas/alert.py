from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertCreate(BaseModel):
    location_id: int
    title: str
    message: str
    risk_level: str
    risk_score: float | None = None
    expires_at: datetime | None = None


class AlertResponse(AlertCreate):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)