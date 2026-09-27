from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Shelter(Base):
    __tablename__ = "shelters"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    address: Mapped[str | None] = mapped_column(
        String(300),
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

    capacity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    contact_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )