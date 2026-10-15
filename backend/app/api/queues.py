from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.queues import QueueItem, QueueStatus
from app.models.journeys import Journey
from app.models.users import User, UserRole
from app.auth.rbac import get_current_user, require_roles
from app.schemas.queue import QueueItemOut

router = APIRouter(prefix="/queues", tags=["Queue Management"])

@router.get("", response_model=List[QueueItemOut])
def get_site_queue(
    site_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(QueueItem).filter(QueueItem.status == QueueStatus.WAITING)
    if site_id:
        query = query.filter(QueueItem.site_id == site_id)
    elif current_user.role in [UserRole.OPERATOR, UserRole.SITE_MANAGER] and current_user.site_id:
        query = query.filter(QueueItem.site_id == current_user.site_id)

    items = query.order_by(QueueItem.position.asc()).all()

    now = datetime.utcnow()
    result = []
    for item in items:
        wait_sec = int((now - item.entry_time).total_seconds())
        result.append(QueueItemOut(
            id=item.id,
            site_id=item.site_id,
            journey_id=item.journey_id,
            vehicle_id=item.vehicle_id,
            vehicle_number=item.vehicle.vehicle_number if item.vehicle else "",
            position=item.position,
            entry_time=item.entry_time,
            wait_time_seconds=wait_sec,
            priority=item.priority,
            status=item.status.value,
            eligibility_status="ELIGIBLE"
        ))
    return result
