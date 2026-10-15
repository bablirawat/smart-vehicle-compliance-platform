from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.bays import Bay, BayStatus
from app.models.journeys import Journey, JourneyState
from app.models.users import User, UserRole
from app.auth.rbac import get_current_user, require_roles
from app.schemas.bay import BayOut, BayAssignRequest, BayStatusUpdateRequest
from app.services.bay_service import bay_service
from app.services.journey_service import journey_service
from app.services.queue_service import queue_service

router = APIRouter(prefix="/bays", tags=["Bay Management"])

@router.get("", response_model=List[BayOut])
def list_bays(
    site_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Bay)
    if site_id:
        query = query.filter(Bay.site_id == site_id)
    elif current_user.role in [UserRole.OPERATOR, UserRole.SITE_MANAGER] and current_user.site_id:
        query = query.filter(Bay.site_id == current_user.site_id)

    bays = query.order_by(Bay.id.asc()).all()

    res = []
    for b in bays:
        v_num = b.current_journey.vehicle.vehicle_number if (b.current_journey and b.current_journey.vehicle) else None
        res.append(BayOut(
            id=b.id,
            site_id=b.site_id,
            bay_name=b.bay_name,
            bay_type=b.bay_type,
            status=b.status.value,
            current_journey_id=b.current_journey_id,
            current_vehicle_number=v_num,
            updated_at=b.updated_at
        ))
    return res

@router.post("/{bay_id}/assign")
def assign_bay_manually(
    bay_id: int,
    payload: BayAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.SITE_MANAGER, UserRole.ADMIN]))
):
    bay = db.query(Bay).filter(Bay.id == bay_id).first()
    if not bay:
        raise HTTPException(status_code=404, detail=f"Bay #{bay_id} not found.")

    if bay.status in [BayStatus.OCCUPIED, BayStatus.MAINTENANCE, BayStatus.BLOCKED]:
        raise HTTPException(status_code=400, detail=f"Bay #{bay.bay_name} is currently in state '{bay.status.value}' and cannot be assigned.")

    journey = db.query(Journey).filter(Journey.id == payload.journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey #{payload.journey_id} not found.")

    # Concurrency safe assignment
    bay.status = BayStatus.RESERVED
    bay.current_journey_id = journey.id
    db.commit()

    journey_service.transition_state(
        db=db,
        journey_id=journey.id,
        target_state=JourneyState.BAY_ASSIGNED,
        user=current_user,
        reason=f"Manually assigned to Bay '{bay.bay_name}' by operator"
    )
    queue_service.dequeue(db, journey.id)

    return {"success": True, "bay_id": bay.id, "bay_name": bay.bay_name, "journey_id": journey.id}

@router.post("/{bay_id}/release")
def release_bay_manually(
    bay_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.SITE_MANAGER, UserRole.ADMIN]))
):
    bay = db.query(Bay).filter(Bay.id == bay_id).first()
    if not bay:
        raise HTTPException(status_code=404, detail="Bay not found.")
    bay.status = BayStatus.AVAILABLE
    bay.current_journey_id = None
    db.commit()
    return {"success": True, "message": f"Bay '{bay.bay_name}' released and marked AVAILABLE."}

@router.post("/{bay_id}/status")
def update_bay_status(
    bay_id: int,
    payload: BayStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SITE_MANAGER, UserRole.ADMIN]))
):
    bay = db.query(Bay).filter(Bay.id == bay_id).first()
    if not bay:
        raise HTTPException(status_code=404, detail="Bay not found.")
    bay.status = BayStatus[payload.status]
    db.commit()
    return {"success": True, "bay_id": bay.id, "new_status": bay.status.value}
