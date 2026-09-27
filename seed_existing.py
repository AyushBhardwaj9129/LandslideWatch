"""
Seed sample data for your EXISTING location (id=1, Guwahati Monitoring Zone).
Run from the backend folder with:  python seed_existing.py
"""

from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.location import Location
from app.models.environmental_data import EnvironmentalData
from app.models.sensor import Sensor
from app.models.alert import Alert
from app.models.shelter import Shelter
from app.models.road import Road
from app.models.population import Population

LOCATION_ID = 1

db = SessionLocal()

try:
    loc = db.query(Location).filter(Location.id == LOCATION_ID).first()
    if loc is None:
        print(f"No location with id={LOCATION_ID} found. Aborting.")
    else:
        print(f"Seeding data for: {loc.name}, {loc.state}")

        now = datetime.utcnow()

        # Environmental data: last 24 hours, hourly
        if db.query(EnvironmentalData).filter(EnvironmentalData.location_id == LOCATION_ID).count() == 0:
            for hours_ago in range(24, 0, -1):
                timestamp = now - timedelta(hours=hours_ago)
                variation = (hours_ago % 5) * 3
                env = EnvironmentalData(
                    location_id=LOCATION_ID,
                    rainfall_mm=max(65 - variation, 5),
                    rainfall_24h_mm=260,
                    rainfall_7d_mm=980,
                    soil_moisture=min(60 + variation * 1.5, 95),
                    temperature=22 + (hours_ago % 6),
                    humidity=70 + (hours_ago % 20),
                    recorded_at=timestamp,
                )
                db.add(env)
            db.commit()
            print("Created 24h of environmental data.")
        else:
            print("Environmental data already exists — skipping.")

        # Sensor
        if db.query(Sensor).filter(Sensor.location_id == LOCATION_ID).count() == 0:
            db.add(Sensor(
                sensor_id=f"SENSOR-{LOCATION_ID:03d}",
                location_id=LOCATION_ID,
                sensor_type="rain_gauge",
                latitude=loc.latitude,
                longitude=loc.longitude,
                is_active=True,
                last_seen=now,
            ))
            db.commit()
            print("Created sensor.")
        else:
            print("Sensor already exists — skipping.")

        # Alert
        if db.query(Alert).filter(Alert.location_id == LOCATION_ID).count() == 0:
            db.add(Alert(
                location_id=LOCATION_ID,
                title=f"Heavy rainfall warning — {loc.name}",
                message="Sustained heavy rainfall and rising soil saturation detected in this area.",
                risk_level="HIGH",
                risk_score=72.5,
                is_active=True,
                created_at=now - timedelta(hours=2),
                expires_at=now + timedelta(hours=22),
            ))
            db.commit()
            print("Created alert.")
        else:
            print("Alert already exists — skipping.")

        # Shelter
        if db.query(Shelter).count() == 0:
            db.add(Shelter(
                name="Guwahati Relief Center",
                address="Ambari, Guwahati",
                latitude=loc.latitude,
                longitude=loc.longitude,
                capacity=300,
                contact_number="+91-9000000002",
                is_active=True,
            ))
            db.commit()
            print("Created shelter.")
        else:
            print("Shelters already exist — skipping.")

        # Road
        if db.query(Road).filter(Road.location_id == LOCATION_ID).count() == 0:
            db.add(Road(
                name="GS Road, Guwahati",
                location_id=LOCATION_ID,
                latitude=loc.latitude,
                longitude=loc.longitude,
                risk_score=35.0,
                risk_level="MODERATE",
                is_blocked=False,
            ))
            db.commit()
            print("Created road.")
        else:
            print("Roads already exist — skipping.")

        # Population
        if db.query(Population).filter(Population.location_id == LOCATION_ID).count() == 0:
            db.add(Population(
                location_id=LOCATION_ID,
                population_count=957352,
                vulnerable_population=120000,
                risk_score=45.0,
            ))
            db.commit()
            print("Created population record.")
        else:
            print("Population record already exists — skipping.")

        print("\nDone. Refresh the dashboard and select Guwahati Monitoring Zone.")
        print("Click 'Recalculate' on the AI Risk Breakdown panel to generate a live prediction.")

finally:
    db.close()
