from sqlalchemy.orm import Session

from app.models.environmental_data import EnvironmentalData


def get_current_weather(
    db: Session,
    location_id: int,
):
    return (
        db.query(EnvironmentalData)
        .filter(
            EnvironmentalData.location_id == location_id
        )
        .order_by(
            EnvironmentalData.recorded_at.desc()
        )
        .first()
    )


def get_weather_history(
    db: Session,
    location_id: int,
    hours: int = 24,
):
    from datetime import datetime, timedelta

    start_time = datetime.utcnow() - timedelta(hours=hours)

    return (
        db.query(EnvironmentalData)
        .filter(
            EnvironmentalData.location_id == location_id,
            EnvironmentalData.recorded_at >= start_time,
        )
        .order_by(
            EnvironmentalData.recorded_at.asc()
        )
        .all()
    )