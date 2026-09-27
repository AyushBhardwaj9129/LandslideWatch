"""
Seed sample data into landslide.db so the dashboard has something to show.
Run from the backend folder with:  python seed.py
Safe to re-run — it checks for existing data before inserting.
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

db = SessionLocal()

try:
    if db.query(Location).count() > 0:
        print("Locations already exist — skipping seed to avoid duplicates.")
        print("Delete landslide.db and restart the server first if you want a clean reseed.")
    else:
        locations_data = [
            {"name": "Itanagar", "state": "Arunachal Pradesh", "district": "Papum Pare", "latitude": 27.0844, "longitude": 93.6053, "elevation": 440},
            {"name": "Guwahati", "state": "Assam", "district": "Kamrup", "latitude": 26.1445, "longitude": 91.7362, "elevation": 55},
            {"name": "Shillong", "state": "Meghalaya", "district": "East Khasi Hills", "latitude": 25.5788, "longitude": 91.8933, "elevation": 1496},
            {"name": "Kohima", "state": "Nagaland", "district": "Kohima", "latitude": 25.6751, "longitude": 94.1086, "elevation": 1444},
            {"name": "Imphal", "state": "Manipur", "district": "Imphal West", "latitude": 24.8170, "longitude": 93.9368, "elevation": 786},
        ]

        locations = []
        for data in locations_data:
            loc = Location(**data)
            db.add(loc)
            locations.append(loc)

        db.commit()
        for loc in locations:
            db.refresh(loc)

        print(f"Created {len(locations)} locations.")

        # Environmental data: last 24 hours, hourly, for each location
        now = datetime.utcnow()
        rainfall_profiles = [65, 82, 40, 28, 55]  # base rainfall per location, mm

        for i, loc in enumerate(locations):
            base_rain = rainfall_profiles[i]
            for hours_ago in range(24, 0, -1):
                timestamp = now - timedelta(hours=hours_ago)
                variation = (hours_ago % 5) * 3
                env = EnvironmentalData(
                    location_id=loc.id,
                    rainfall_mm=max(base_rain - variation, 5),
                    rainfall_24h_mm=base_rain * 4,
                    rainfall_7d_mm=base_rain * 15,
                    soil_moisture=min(60 + variation * 1.5, 95),
                    temperature=22 + (hours_ago % 6),
                    humidity=70 + (hours_ago % 20),
                    recorded_at=timestamp,
                )
                db.add(env)

        db.commit()
        print("Created 24h of environmental data per location.")

        # Sensors
        for i, loc in enumerate(locations):
            sensor = Sensor(
                sensor_id=f"SENSOR-{loc.id:03d}",
                location_id=loc.id,
                sensor_type="rain_gauge",
                latitude=loc.latitude,
                longitude=loc.longitude,
                is_active=True,
                last_seen=now,
            )
            db.add(sensor)
        db.commit()
        print("Created sensors.")

        # Alerts (only for the higher-rainfall locations)
        alert_locations = [locations[0], locations[1]]
        for loc in alert_locations:
            alert = Alert(
                location_id=loc.id,
                title=f"Heavy rainfall warning — {loc.name}",
                message="Sustained heavy rainfall and rising soil saturation detected in this area.",
                risk_level="HIGH",
                risk_score=72.5,
                is_active=True,
                created_at=now - timedelta(hours=2),
                expires_at=now + timedelta(hours=22),
            )
            db.add(alert)
        db.commit()
        print("Created sample alerts.")

        # Shelters
        shelters_data = [
            {"name": "Itanagar Community Hall", "address": "Near Ganga Market, Itanagar", "latitude": 27.086, "longitude": 93.607, "capacity": 150, "contact_number": "+91-9000000001"},
            {"name": "Guwahati Relief Center", "address": "Ambari, Guwahati", "latitude": 26.146, "longitude": 91.738, "capacity": 300, "contact_number": "+91-9000000002"},
            {"name": "Shillong Emergency Shelter", "address": "Police Bazar, Shillong", "latitude": 25.579, "longitude": 91.894, "capacity": 100, "contact_number": "+91-9000000003"},
        ]
        for s in shelters_data:
            db.add(Shelter(**s, is_active=True))
        db.commit()
        print("Created shelters.")

        # Roads
        roads_data = [
            {"name": "NH-15 near Itanagar", "location_id": locations[0].id, "latitude": 27.09, "longitude": 93.61, "risk_score": 78.0, "risk_level": "HIGH"},
            {"name": "GS Road, Guwahati", "location_id": locations[1].id, "latitude": 26.15, "longitude": 91.74, "risk_score": 35.0, "risk_level": "MODERATE"},
            {"name": "Shillong-Guwahati Highway", "location_id": locations[2].id, "latitude": 25.58, "longitude": 91.90, "risk_score": 82.0, "risk_level": "CRITICAL", "is_blocked": True},
        ]
        for r in roads_data:
            db.add(Road(**r))
        db.commit()
        print("Created roads.")

        # Population vulnerability
        population_data = [
            {"location_id": locations[0].id, "population_count": 59490, "vulnerable_population": 8200, "risk_score": 60.0},
            {"location_id": locations[1].id, "population_count": 957352, "vulnerable_population": 120000, "risk_score": 45.0},
            {"location_id": locations[2].id, "population_count": 143229, "vulnerable_population": 21000, "risk_score": 70.0},
        ]
        for p in population_data:
            db.add(Population(**p))
        db.commit()
        print("Created population records.")

        print("\nSeed complete. Refresh the dashboard — pick a location from the dropdown")
        print("and click 'Recalculate' on the AI Risk Breakdown panel to generate a live prediction.")

finally:
    db.close()
