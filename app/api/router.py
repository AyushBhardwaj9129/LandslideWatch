from fastapi import APIRouter
 
from app.api.v1.auth import router as auth_router
from app.api.v1.locations import router as locations_router
from app.api.v1.environmental_data import (
    router as environmental_data_router,
)
from app.api.v1.rainfall import (
    router as rainfall_router,
)
from app.api.v1.soil_moisture import (
    router as soil_moisture_router,
)
from app.api.v1.weather import (
    router as weather_router,
)
from app.api.v1.sensors import (
    router as sensors_router,
)
from app.api.v1.alerts import (
    router as alerts_router,
)
from app.api.v1.risk import (
    router as risk_router,
)
from app.api.v1.roads import (
    router as roads_router,
)
from app.api.v1.shelters import (
    router as shelters_router,
)
from app.api.v1.population import (
    router as population_router,
)
 
 
api_router = APIRouter()
 
api_router.include_router(auth_router)
api_router.include_router(locations_router)
api_router.include_router(environmental_data_router)
api_router.include_router(rainfall_router)
api_router.include_router(soil_moisture_router)
api_router.include_router(weather_router)
api_router.include_router(sensors_router)
api_router.include_router(alerts_router)
api_router.include_router(risk_router)
api_router.include_router(roads_router)
api_router.include_router(shelters_router)
api_router.include_router(population_router)
 