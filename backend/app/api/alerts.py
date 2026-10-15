from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.alerts import Alert, AlertStatus, AlertSeverity
from app.models.users import User, UserRole
from app.auth.rbac import get_current_user, require_roles
from app.schemas.alert import AlertOut, AlertActionRequest
from app.services.alert_service import alert_service

router = APIRouter(prefix="/alerts", tags=["Alert Management"])

@router.get("", response_model=List[AlertOut])
def list_alerts(
    site_id: Optional[int] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Alert)
    if site_id:
        query = query.filter(Alert.site_id == site_id)
    elif current_user.role in [UserRole.OPERATOR, UserRole.SITE_MANAGER] and current_user.site_id:
        query = query.filter(Alert.site_id == current_user.site_id)

    if status:
        query = query.filter(Alert.status == AlertStatus[status])
    if severity:
        query = query.filter(Alert.severity == AlertSeverity[severity])

    alerts = query.order_by(Alert.created_at.desc()).limit(100).all()

    res = []
    for a in alerts:
        v_num = a.journey.vehicle.vehicle_number if (a.journey and a.journey.vehicle) else None
        ack_name = a.acknowledged_user.full_name if a.acknowledged_user else None
        res_name = a.resolved_user.full_name if a.resolved_user else None
        res.append(AlertOut(
            id=a.id,
            site_id=a.site_id,
            site_name=a.site.name if a.site else None,
            journey_id=a.journey_id,
            vehicle_number=v_num,
            alert_type=a.alert_type,
            severity=a.severity.value,
            message=a.message,
            status=a.status.value,
            acknowledged_by=a.acknowledged_by,
            acknowledged_by_name=ack_name,
            resolved_by=a.resolved_by,
            resolved_by_name=res_name,
            created_at=a.created_at,
            resolved_at=a.resolved_at
        ))
    return res

@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.SITE_MANAGER, UserRole.REGIONAL_MANAGER, UserRole.ADMIN]))
):
    try:
        updated = alert_service.acknowledge_alert(db, alert_id, current_user)
        return {"success": True, "alert_id": updated.id, "status": updated.status.value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    payload: AlertActionRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.SITE_MANAGER, UserRole.REGIONAL_MANAGER, UserRole.ADMIN]))
):
    try:
        notes = payload.notes if payload else None
        updated = alert_service.resolve_alert(db, alert_id, current_user, notes=notes)
        return {"success": True, "alert_id": updated.id, "status": updated.status.value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
