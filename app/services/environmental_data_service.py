from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.environmental_data import EnvironmentalData


def create_environmental_data(
    db: Session,
    location_id: int,
    rainfall_mm: float | None = None,
    rainfall_intensity: float | None = None,
    soil_moisture: float | None = None,
    temperature: float | None = None,
    humidity: float | None = None,
):
    data = EnvironmentalData(
        location_id=location_id,
        rainfall_mm=rainfall_mm,
        soil_moisture=soil_moisture,
        temperature=temperature,
        humidity=humidity,
    )

    db.add(data)
    db.commit()
    db.refresh(data)

    return data


def get_latest_environmental_data(
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


def get_environmental_history(
    db: Session,
    location_id: int,
    hours: int = 24,
):
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