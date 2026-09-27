from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Population(Base):
    __tablename__ = "population"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"),
        nullable=False,
        index=True
    )

    population_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    vulnerable_population: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    risk_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
