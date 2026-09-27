from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    CurrentUserResponse,
)

from app.schemas.user import (
    UserCreate,
    UserResponse,
)

from app.schemas.location import (
    LocationCreate,
    LocationResponse,
)

from app.schemas.environmental_data import (
    EnvironmentalDataCreate,
    EnvironmentalDataResponse,
)

from app.schemas.sensor import (
    SensorCreate,
    SensorReading,
    SensorResponse,
)

from app.schemas.landslide import (
    LandslideCreate,
    LandslideResponse,
)

from app.schemas.risk import (
    RiskPredictionRequest,
    RiskPredictionResponse,
)

from app.schemas.forecast import (
    RiskForecastResponse,
)

from app.schemas.alert import (
    AlertCreate,
    AlertResponse,
)

from app.schemas.road import (
    RoadCreate,
    RoadResponse,
)

from app.schemas.population import (
    PopulationCreate,
    PopulationResponse,
)

from app.schemas.shelter import (
    ShelterCreate,
    ShelterResponse,
)

from app.schemas.trend import (
    TrendDataPoint,
    EnvironmentalTrendResponse,
)

from app.schemas.recommendation import (
    RecommendationResponse,
)

from app.schemas.weather import (
    WeatherResponse,
)


__all__ = [
    "LoginRequest",
    "TokenResponse",
    "CurrentUserResponse",
    "UserCreate",
    "UserResponse",
    "LocationCreate",
    "LocationResponse",
    "EnvironmentalDataCreate",
    "EnvironmentalDataResponse",
    "SensorCreate",
    "SensorReading",
    "SensorResponse",
    "LandslideCreate",
    "LandslideResponse",
    "RiskPredictionRequest",
    "RiskPredictionResponse",
    "RiskForecastResponse",
    "AlertCreate",
    "AlertResponse",
    "RoadCreate",
    "RoadResponse",
    "PopulationCreate",
    "PopulationResponse",
    "ShelterCreate",
    "ShelterResponse",
    "TrendDataPoint",
    "EnvironmentalTrendResponse",
    "RecommendationResponse",
    "WeatherResponse",
]