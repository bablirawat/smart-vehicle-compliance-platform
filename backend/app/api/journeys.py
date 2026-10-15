from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.journeys import Journey, JourneyState
from app.models.vehicles import Vehicle
from app.models.bays import Bay
from app.models.queues import QueueItem
from app.models.users import User, UserRole
from app.auth.rbac import get_current_user, require_roles
from app.schemas.journey import JourneyOut, JourneyDetailOut, TransitionRequest, HoldReleaseRequest, OverrideRequest
from app.services.journey_service import journey_service
from app.services.verification_service import VerificationService
from app.services.audit_service import AuditService
from app.state_machine.journey_state_machine import InvalidStateTransitionException

router = APIRouter(prefix="/journeys", tags=["Journeys"])

@router.get("", response_model=List[JourneyOut])
def list_journeys(
    site_id: Optional[int] = None,
    state: Optional[str] = None,
    vehicle_number: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Journey).join(Vehicle)
    if site_id:
        query = query.filter(Journey.site_id == site_id)
    elif current_user.role in [UserRole.OPERATOR, UserRole.SITE_MANAGER] and current_user.site_id:
        query = query.filter(Journey.site_id == current_user.site_id)
    
    if state:
        query = query.filter(Journey.current_state == JourneyState[state])
    if vehicle_number:
        query = query.filter(Vehicle.vehicle_number.ilike(f"%{vehicle_number}%"))

    journeys = query.order_by(Journey.entry_time.desc()).limit(100).all()

    result = []
    for j in journeys:
        result.append(JourneyOut(
            id=j.id,
            vehicle_id=j.vehicle_id,
            vehicle_number=j.vehicle.vehicle_number if j.vehicle else "",
            site_id=j.site_id,
            site_name=j.site.name if j.site else "",
            entry_camera_id=j.entry_camera_id,
            exit_camera_id=j.exit_camera_id,
            current_state=j.current_state,
            anpr_confidence=j.anpr_confidence,
            entry_time=j.entry_time,
            bay_assigned_time=j.bay_assigned_time,
            service_start_time=j.service_start_time,
            service_end_time=j.service_end_time,
            exit_time=j.exit_time,
            created_at=j.created_at,
            updated_at=j.updated_at
        ))
    return result

@router.get("/{journey_id}", response_model=JourneyDetailOut)
def get_journey_detail(journey_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    journey = db.query(Journey).filter(Journey.id == journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail=f"Journey #{journey_id} not found.")

    bay = db.query(Bay).filter(Bay.current_journey_id == journey.id).first()
    q_item = db.query(QueueItem).filter(QueueItem.journey_id == journey.id).first()

    return JourneyDetailOut(
        id=journey.id,
        vehicle_id=journey.vehicle_id,
        vehicle_number=journey.vehicle.vehicle_number if journey.vehicle else "",
        vehicle_make=journey.vehicle.make if journey.vehicle else None,
        vehicle_model=journey.vehicle.model if journey.vehicle else None,
        vehicle_category=journey.vehicle.category if journey.vehicle else None,
        site_id=journey.site_id,
        site_name=journey.site.name if journey.site else "",
        entry_camera_id=journey.entry_camera_id,
        exit_camera_id=journey.exit_camera_id,
        current_state=journey.current_state,
        anpr_confidence=journey.anpr_confidence,
        entry_time=journey.entry_time,
        bay_assigned_time=journey.bay_assigned_time,
        service_start_time=journey.service_start_time,
        service_end_time=journey.service_end_time,
        exit_time=journey.exit_time,
        created_at=journey.created_at,
        updated_at=journey.updated_at,
        queue_position=q_item.position if q_item else None,
        assigned_bay_name=bay.bay_name if bay else None,
        events=[{
            "id": e.id,
            "journey_id": e.journey_id,
            "vehicle_id": e.vehicle_id,
            "site_id": e.site_id,
            "previous_state": e.previous_state,
            "new_state": e.new_state,
            "event_source": e.event_source,
            "evidence_data": e.evidence_data,
            "operator_id": e.operator_id,
            "reason": e.reason,
            "timestamp": e.timestamp
        } for e in sorted(journey.events, key=lambda x: x.timestamp)],
        verifications=[{
            "id": v.id,
            "verification_type": v.verification_type.value,
            "source": v.source,
            "status": v.status.value,
            "details": v.details,
            "error_message": v.error_message,
            "timestamp": v.timestamp
        } for v in journey.verifications]
    )

@router.post("/{journey_id}/transition")
def transition_journey(
    journey_id: int,
    payload: TransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.SITE_MANAGER, UserRole.ADMIN]))
):
    try:
        updated = journey_service.transition_state(
            db=db,
            journey_id=journey_id,
            target_state=payload.target_state,
            user=current_user,
            reason=payload.reason
        )
        return {"success": True, "journey_id": updated.id, "current_state": updated.current_state.value}
    except InvalidStateTransitionException as err:
        raise HTTPException(status_code=422, detail={"code": "INVALID_STATE_TRANSITION", "message": err.reason})

@router.post("/{journey_id}/hold")
def hold_journey(
    journey_id: int,
    payload: HoldReleaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.SITE_MANAGER, UserRole.ADMIN]))
):
    try:
        updated = journey_service.transition_state(
            db=db,
            journey_id=journey_id,
            target_state=JourneyState.HOLD,
            user=current_user,
            reason=payload.reason
        )
        return {"success": True, "journey_id": updated.id, "current_state": updated.current_state.value}
    except InvalidStateTransitionException as err:
        raise HTTPException(status_code=422, detail={"code": "INVALID_STATE_TRANSITION", "message": err.reason})

@router.post("/{journey_id}/release")
def release_journey(
    journey_id: int,
    payload: HoldReleaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.SITE_MANAGER, UserRole.ADMIN]))
):
    try:
        updated = journey_service.transition_state(
            db=db,
            journey_id=journey_id,
            target_state=JourneyState.QUEUED,
            user=current_user,
            reason=payload.reason
        )
        return {"success": True, "journey_id": updated.id, "current_state": updated.current_state.value}
    except InvalidStateTransitionException as err:
        raise HTTPException(status_code=422, detail={"code": "INVALID_STATE_TRANSITION", "message": err.reason})

@router.post("/{journey_id}/override")
def override_journey_state(
    journey_id: int,
    payload: OverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SITE_MANAGER, UserRole.REGIONAL_MANAGER, UserRole.ADMIN]))
):
    if not payload.reason or len(payload.reason.strip()) < 5:
        raise HTTPException(status_code=400, detail="Authorized override requires a detailed reason (minimum 5 characters).")
    try:
        updated = journey_service.transition_state(
            db=db,
            journey_id=journey_id,
            target_state=payload.target_state,
            user=current_user,
            reason=f"[OPERATOR OVERRIDE]: {payload.reason}",
            is_override=True
        )
        return {"success": True, "journey_id": updated.id, "current_state": updated.current_state.value}
    except InvalidStateTransitionException as err:
        raise HTTPException(status_code=422, detail={"code": "INVALID_STATE_TRANSITION", "message": err.reason})

@router.post("/{journey_id}/verify")
def retrigger_verification(
    journey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.SITE_MANAGER, UserRole.ADMIN]))
):
    journey = db.query(Journey).filter(Journey.id == journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found.")

    v_ident = VerificationService.verify_identity(db, journey.id, journey.vehicle, simulated_override_status="VALID")
    v_comp = VerificationService.verify_compliance(db, journey.id, journey.vehicle, simulated_override_status="VALID")

    journey.current_state = JourneyState.ELIGIBLE
    db.commit()

    AuditService.log(
        db=db,
        action="REVERIFICATION_PERFORMED",
        event_type="VERIFICATION",
        user=current_user,
        site_id=journey.site_id,
        vehicle_number=journey.vehicle.vehicle_number,
        new_state="ELIGIBLE"
    )

    return {"success": True, "message": "Manual re-verification completed successfully. Vehicle state set to ELIGIBLE."}
