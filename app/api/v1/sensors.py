from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.location import Location
from app.schemas.sensor import (
    SensorCreate,
    SensorReading,
    SensorResponse,
)
from app.services.sensor_service import (
    create_sensor,
    get_sensor,
    get_sensors,
    record_sensor_reading,
)


router = APIRouter(
    prefix="/sensors",
    tags=["Sensors"],
)


@router.post(
    "/",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_sensor(
    sensor_data: SensorCreate,
    db: Session = Depends(get_db),
):
    location = db.query(Location).filter(
        Location.id == sensor_data.location_id
    ).first()

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Location not found",
        )

    existing_sensor = get_sensor(
        db,
        sensor_data.sensor_id,
    )

    if existing_sensor:
        raise HTTPException(
            status_code=400,
            detail="Sensor ID already exists",
        )

    return create_sensor(
        db=db,
        sensor_id=sensor_data.sensor_id,
        location_id=sensor_data.location_id,
        sensor_type=sensor_data.sensor_type,
        latitude=sensor_data.latitude,
        longitude=sensor_data.longitude,
    )


@router.get(
    "/",
    response_model=list[SensorResponse],
)
def get_all_sensors(
    location_id: int | None = None,
    db: Session = Depends(get_db),
):
    return get_sensors(
        db,
        location_id,
    )


@router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
)
def get_sensor_by_id(
    sensor_id: str,
    db: Session = Depends(get_db),
):
    sensor = get_sensor(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=404,
            detail="Sensor not found",
        )

    return sensor
@router.post(
    "/{sensor_id}/readings",
)
def submit_sensor_reading(
    sensor_id: str,
    reading: SensorReading,
    db: Session = Depends(get_db),
):
    sensor = get_sensor(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=404,
            detail="Sensor not found",
        )

    if not sensor.is_active:
        raise HTTPException(
            status_code=400,
            detail="Sensor is inactive",
        )

    data = record_sensor_reading(
        db=db,
        sensor=sensor,
        rainfall_mm=reading.rainfall_mm,
        soil_moisture=reading.soil_moisture,
        temperature=reading.temperature,
        humidity=reading.humidity,
        recorded_at=reading.recorded_at,
    )

    return {
        "message": "Sensor reading recorded successfully",
        "sensor_id": sensor.sensor_id,
        "location_id": sensor.location_id,
        "recorded_at": data.recorded_at,
    }
@router.get(
    "/{sensor_id}/readings",
)
def get_sensor_readings(
    sensor_id: str,
    hours: int = 24,
    db: Session = Depends(get_db),
):
    from app.services.environmental_data_service import (
        get_environmental_history,
    )

    sensor = get_sensor(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=404,
            detail="Sensor not found",
        )

    data = get_environmental_history(
        db,
        sensor.location_id,
        hours,
    )

    return {
        "sensor_id": sensor.sensor_id,
        "location_id": sensor.location_id,
        "hours": hours,
        "data": [
            {
                "timestamp": item.recorded_at,
                "rainfall_mm": item.rainfall_mm,
                "soil_moisture": item.soil_moisture,
                "temperature": item.temperature,
                "humidity": item.humidity,
            }
            for item in data
        ],
    }
@router.patch(
    "/{sensor_id}/status",
)
def update_sensor_status(
    sensor_id: str,
    is_active: bool,
    db: Session = Depends(get_db),
):
    sensor = get_sensor(
        db,
        sensor_id,
    )

    if sensor is None:
        raise HTTPException(
            status_code=404,
            detail="Sensor not found",
        )

    sensor.is_active = is_active

    db.commit()
    db.refresh(sensor)

    return {
        "message": "Sensor status updated",
        "sensor_id": sensor.sensor_id,
        "is_active": sensor.is_active,
    }