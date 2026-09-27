from datetime import datetime

from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EnvironmentalData(Base):
    __tablename__ = "environmental_data"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False,
        index=True
    )

    rainfall_mm: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    rainfall_24h_mm: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    rainfall_7d_mm: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    soil_moisture: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )

    temperature: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    humidity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    recorded_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    location = relationship(
        "Location",
        back_populates="environmental_data"
    )