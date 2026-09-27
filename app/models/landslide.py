from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Landslide(Base):
    __tablename__ = "landslides"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    severity: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )