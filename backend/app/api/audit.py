import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit import AuditLog
from app.models.users import User, UserRole
from app.auth.rbac import get_current_user, require_roles
from app.schemas.audit import AuditLogOut

router = APIRouter(prefix="/audit", tags=["Audit Logging"])

@router.get("", response_model=List[AuditLogOut])
def get_audit_logs(
    site_id: Optional[int] = None,
    vehicle_number: Optional[str] = None,
    event_type: Optional[str] = None,
    user_email: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AuditLog)
    if site_id:
        query = query.filter(AuditLog.site_id == site_id)
    elif current_user.role in [UserRole.OPERATOR, UserRole.SITE_MANAGER] and current_user.site_id:
        query = query.filter(AuditLog.site_id == current_user.site_id)

    if vehicle_number:
        query = query.filter(AuditLog.vehicle_number.ilike(f"%{vehicle_number}%"))
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if user_email:
        query = query.filter(AuditLog.user_email.ilike(f"%{user_email}%"))

    logs = query.order_by(AuditLog.timestamp.desc()).limit(200).all()

    res = []
    for l in logs:
        res.append(AuditLogOut(
            id=l.id,
            user_id=l.user_id,
            user_email=l.user_email,
            role=l.role,
            action=l.action,
            site_id=l.site_id,
            site_name=l.site.name if l.site else None,
            vehicle_number=l.vehicle_number,
            previous_state=l.previous_state,
            new_state=l.new_state,
            reason=l.reason,
            event_type=l.event_type,
            timestamp=l.timestamp
        ))
    return res

@router.get("/export")
def export_audit_logs_csv(
    site_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.AUDITOR, UserRole.SITE_MANAGER, UserRole.REGIONAL_MANAGER, UserRole.ADMIN]))
):
    query = db.query(AuditLog)
    if site_id:
        query = query.filter(AuditLog.site_id == site_id)

    logs = query.order_by(AuditLog.timestamp.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Timestamp", "User Email", "Role", "Action", "Event Type",
        "Site ID", "Vehicle Number", "Previous State", "New State", "Reason"
    ])

    for l in logs:
        writer.writerow([
            l.id,
            l.timestamp.isoformat(),
            l.user_email or "SYSTEM",
            l.role or "SYSTEM",
            l.action,
            l.event_type,
            l.site_id or "",
            l.vehicle_number or "",
            l.previous_state or "",
            l.new_state or "",
            l.reason or ""
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )
