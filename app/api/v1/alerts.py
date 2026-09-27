from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
 
from app.core.database import get_db
from app.models.alert import Alert
from app.models.location import Location
from app.schemas.alert import AlertCreate, AlertResponse
 
 
router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)
 
 
@router.post(
    "/",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
):
    location = db.query(Location).filter(
        Location.id == alert_data.location_id
    ).first()
 
    if location is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found",
        )
 
    alert = Alert(
        location_id=alert_data.location_id,
        title=alert_data.title,
        message=alert_data.message,
        risk_level=alert_data.risk_level,
        risk_score=alert_data.risk_score,
        expires_at=alert_data.expires_at,
        is_active=True,
    )
 
    db.add(alert)
    db.commit()
    db.refresh(alert)
 
    return alert
 
 
@router.get(
    "/",
    response_model=list[AlertResponse],
)
def get_alerts(
    location_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Alert)
 
    if location_id is not None:
        query = query.filter(Alert.location_id == location_id)
 
    if is_active is not None:
        query = query.filter(Alert.is_active == is_active)
 
    if risk_level is not None:
        query = query.filter(Alert.risk_level.ilike(risk_level))
 
    return query.order_by(Alert.created_at.desc()).all()
 
 
@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
 
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
 
    return alert
 
 
@router.patch(
    "/{alert_id}/deactivate",
    response_model=AlertResponse,
)
def deactivate_alert(
    alert_id: int,
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
 
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
 
    alert.is_active = False
 
    db.commit()
    db.refresh(alert)
 
    return alert
 