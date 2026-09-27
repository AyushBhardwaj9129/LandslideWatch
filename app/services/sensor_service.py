from datetime import datetime

from sqlalchemy.orm import Session

from app.models.sensor import Sensor
from app.models.environmental_data import EnvironmentalData


def create_sensor(
    db: Session,
    sensor_id: str,
    location_id: int,
    sensor_type: str,
    latitude: float,
    longitude: float,
):
    sensor = Sensor(
        sensor_id=sensor_id,
        location_id=location_id,
        sensor_type=sensor_type,
        latitude=latitude,
        longitude=longitude,
        is_active=True,
    )

    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    return sensor


def get_sensors(
    db: Session,
    location_id: int | None = None,
):
    query = db.query(Sensor)

    if location_id is not None:
        query = query.filter(
            Sensor.location_id == location_id
        )

    return query.all()


def get_sensor(
    db: Session,
    sensor_id: str,
):
    return (
        db.query(Sensor)
        .filter(
            Sensor.sensor_id == sensor_id
        )
        .first()
    )


def record_sensor_reading(
    db: Session,
    sensor: Sensor,
    rainfall_mm: float | None = None,
    soil_moisture: float | None = None,
    temperature: float | None = None,
    humidity: float | None = None,
    recorded_at: datetime | None = None,
):
    environmental_data = EnvironmentalData(
        location_id=sensor.location_id,
        rainfall_mm=rainfall_mm,
        soil_moisture=soil_moisture,
        temperature=temperature,
        humidity=humidity,
        recorded_at=recorded_at or datetime.utcnow(),
    )

    sensor.last_seen = environmental_data.recorded_at

    db.add(environmental_data)
    db.commit()
    db.refresh(environmental_data)

    return environmental_data
