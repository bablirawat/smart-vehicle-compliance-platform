from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.journeys import Journey, JourneyState
from app.models.bays import Bay
from app.models.users import User, UserRole
from app.auth.rbac import get_current_user, require_roles
from app.services.bay_service import bay_service
from app.services.journey_service import journey_service

router = APIRouter(prefix="/service", tags=["Service Lifecycle Management"])

class ServiceStartRequest(BaseModel):
    journey_id: int
    bay_id: int

class ServiceCompleteRequest(BaseModel):
    journey_id: int
    notes: Optional[str] = None

@router.post("/start")
def start_service(
    payload: ServiceStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.SITE_MANAGER, UserRole.ADMIN]))
):
    journey = db.query(Journey).filter(Journey.id == payload.journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found.")

    if journey.current_state != JourneyState.BAY_ASSIGNED:
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle cannot start service from state '{journey.current_state.value}'. Must be in 'BAY_ASSIGNED' state."
        )

    session = bay_service.start_service(
        db=db,
        journey=journey,
        bay_id=payload.bay_id,
        operator_id=current_user.id
    )

    journey_service.transition_state(
        db=db,
        journey_id=journey.id,
        target_state=JourneyState.IN_SERVICE,
        user=current_user,
        reason="Inspection service started by operator"
    )

    return {"success": True, "journey_id": journey.id, "session_id": session.id, "status": "IN_SERVICE"}

@router.post("/complete")
def complete_service(
    payload: ServiceCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.SITE_MANAGER, UserRole.ADMIN]))
):
    journey = db.query(Journey).filter(Journey.id == payload.journey_id).first()
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found.")

    if journey.current_state != JourneyState.IN_SERVICE:
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle service cannot complete from state '{journey.current_state.value}'. Must be in 'IN_SERVICE' state."
        )

    session = bay_service.complete_service(
        db=db,
        journey=journey,
        notes=payload.notes
    )

    journey_service.transition_state(
        db=db,
        journey_id=journey.id,
        target_state=JourneyState.SERVICE_COMPLETED,
        user=current_user,
        reason="Inspection service completed successfully"
    )

    return {"success": True, "journey_id": journey.id, "status": "SERVICE_COMPLETED"}
