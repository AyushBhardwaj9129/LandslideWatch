from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    title: str
    description: str
    priority: str = "MEDIUM"
    action: str | None = None