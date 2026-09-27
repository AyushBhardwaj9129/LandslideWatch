from datetime import datetime, timedelta
from app.services.live_weather_service import get_weather_forecast, get_live_weather
from app.services.live_soil_service import get_live_soil_moisture
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
 
from app.core.database import get_db
from app.models.location import Location
from app.models.risk_prediction import RiskPrediction
from app.models.risk_forecast import RiskForecast
 
 
router = APIRouter(
    prefix="/risk",
    tags=["Risk"],
)
 
MODEL_VERSION = "heuristic-v1"
 
 
def calculate_risk(
    rainfall_24h_mm: float | None,
    soil_moisture: float | None,
    temperature: float | None,
) -> tuple[float, str, str]:
    """
    Transparent weighted heuristic (not a trained ML model):
    - Rainfall (last 24h): 45%, saturating at 200mm
    - Soil moisture: 35%, already a 0-100 scale
    - Temperature: 20%, higher temperature slightly raises
      instability risk in this simplified model
    """
    rainfall_score = min(((rainfall_24h_mm or 0) / 200) * 100, 100)
    soil_score = min(max(soil_moisture or 0, 0), 100)
    temp_score = min(max(((temperature or 20) - 10) * 3, 0), 100)
 
    risk_score = round(
        rainfall_score * 0.45 + soil_score * 0.35 + temp_score * 0.20,
        1,
    )
    risk_score = min(max(risk_score, 0), 100)
 
    if risk_score >= 80:
        risk_level = "CRITICAL"
    elif risk_score >= 60:
        risk_level = "HIGH"
    elif risk_score >= 35:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"
 
    explanation = (
        f"Rainfall (24h) contributed {round(rainfall_score * 0.45, 1)} pts, "
        f"soil moisture contributed {round(soil_score * 0.35, 1)} pts, "
        f"temperature contributed {round(temp_score * 0.20, 1)} pts."
    )
 
    return risk_score, risk_level, explanation
 
 
class RiskPredictRequest(BaseModel):
    location_id: int
 
 
@router.post("/predict")
def predict_risk(
    payload: RiskPredictRequest,
    db: Session = Depends(get_db),
):
    location = db.query(Location).filter(
        Location.id == payload.location_id
    ).first()
 
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
 
    try:
        weather = get_live_weather(location.latitude, location.longitude)
        soil = get_live_soil_moisture(location.latitude, location.longitude)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not fetch live environmental data: {str(e)}",
        )
 
    risk_score, risk_level, explanation = calculate_risk(
        rainfall_24h_mm=weather["rainfall_mm"],
        soil_moisture=soil["soil_moisture"],
        temperature=weather["temperature"],
    )
 
    prediction = RiskPrediction(
        location_id=payload.location_id,
        risk_score=risk_score,
        risk_level=risk_level,
        confidence=0.7,
        explanation=explanation,
        model_version=MODEL_VERSION,
        predicted_at=datetime.utcnow(),
    )
 
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
 
    return {
        "id": prediction.id,
        "location_id": prediction.location_id,
        "risk_score": prediction.risk_score,
        "risk_level": prediction.risk_level,
        "confidence": prediction.confidence,
        "explanation": prediction.explanation,
        "model_version": prediction.model_version,
        "predicted_at": prediction.predicted_at,
    }
 
 
@router.get("/predictions/{location_id}/latest")
def get_latest_prediction(
    location_id: int,
    db: Session = Depends(get_db),
):
    prediction = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.location_id == location_id)
        .order_by(RiskPrediction.predicted_at.desc())
        .first()
    )
 
    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No risk prediction found for this location",
        )
 
    return {
        "id": prediction.id,
        "location_id": prediction.location_id,
        "risk_score": prediction.risk_score,
        "risk_level": prediction.risk_level,
        "confidence": prediction.confidence,
        "explanation": prediction.explanation,
        "model_version": prediction.model_version,
        "predicted_at": prediction.predicted_at,
    }
 
 
@router.get("/predictions/{location_id}/history")
def get_prediction_history(
    location_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    predictions = (
        db.query(RiskPrediction)
        .filter(RiskPrediction.location_id == location_id)
        .order_by(RiskPrediction.predicted_at.desc())
        .limit(limit)
        .all()
    )
 
    return [
        {
            "id": p.id,
            "location_id": p.location_id,
            "risk_score": p.risk_score,
            "risk_level": p.risk_level,
            "confidence": p.confidence,
            "predicted_at": p.predicted_at,
        }
        for p in predictions
    ]
 
 
class ForecastGenerateRequest(BaseModel):
    location_id: int
    hours_ahead: list[int] = [6, 12, 24]
 
 
@router.post("/forecast/generate")
def generate_forecast(
    payload: ForecastGenerateRequest,
    db: Session = Depends(get_db),
):
    location = db.query(Location).filter(
        Location.id == payload.location_id
    ).first()
 
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
 
    try:
        weather = get_live_weather(location.latitude, location.longitude)
        soil = get_live_soil_moisture(location.latitude, location.longitude)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not fetch live environmental data: {str(e)}",
        )
 
    base_score, _, _ = calculate_risk(
        rainfall_24h_mm=weather["rainfall_mm"],
        soil_moisture=soil["soil_moisture"],
        temperature=weather["temperature"],
    )
 
    created = []
    now = datetime.utcnow()
 
    for i, hours in enumerate(payload.hours_ahead):
        # naive decay/growth trend just so the forecast isn't flat;
        # replace with a real time-series model when available
        drift = (i + 1) * 2
        projected_score = min(max(base_score - drift, 0), 100)
 
        if projected_score >= 80:
            level = "CRITICAL"
        elif projected_score >= 60:
            level = "HIGH"
        elif projected_score >= 35:
            level = "MODERATE"
        else:
            level = "LOW"
 
        forecast = RiskForecast(
            location_id=payload.location_id,
            forecast_time=now + timedelta(hours=hours),
            risk_score=round(projected_score, 1),
            risk_level=level,
            confidence=0.5,
            model_version=MODEL_VERSION,
            created_at=now,
        )
        db.add(forecast)
        created.append(forecast)
 
    db.commit()
 
    for f in created:
        db.refresh(f)
 
    return [
        {
            "location_id": f.location_id,
            "forecast_time": f.forecast_time,
            "risk_score": f.risk_score,
            "risk_level": f.risk_level,
            "confidence": f.confidence,
            "model_version": f.model_version,
        }
        for f in created
    ]
 
 
@router.get("/forecast/{location_id}")
def get_forecast(
    location_id: int,
    db: Session = Depends(get_db),
):
    forecasts = (
        db.query(RiskForecast)
        .filter(
            RiskForecast.location_id == location_id,
            RiskForecast.forecast_time >= datetime.utcnow(),
        )
        .order_by(RiskForecast.forecast_time.asc())
        .limit(3)
        .all()
    )

    return [
        {
            "location_id": f.location_id,
            "forecast_time": f.forecast_time,
            "risk_score": f.risk_score,
            "risk_level": f.risk_level,
            "confidence": f.confidence,
        }
        for f in forecasts
    ]