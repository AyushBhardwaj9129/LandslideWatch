from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False,
        index=True
    )

    risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    model_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    predicted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True,
        nullable=False
    )