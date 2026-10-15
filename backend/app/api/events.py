from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.event import VehicleEntryEvent, VehicleExitEvent, EventResponse
from app.services.journey_service import journey_service
from app.models.users import User, UserRole
from app.auth.rbac import get_current_user

router = APIRouter(prefix="/events", tags=["Vehicle Events & ANPR Simulator"])

@router.post("/vehicle-entry", response_model=EventResponse)
def handle_vehicle_entry(payload: VehicleEntryEvent, db: Session = Depends(get_db)):
    try:
        journey, is_duplicate = journey_service.process_vehicle_entry(
            db=db,
            site_id=payload.site_id,
            camera_id=payload.camera_id,
            vehicle_number=payload.vehicle_number,
            confidence=payload.confidence,
            timestamp=payload.timestamp
        )
        msg = "Duplicate entry suppressed within deduplication window" if is_duplicate else "Vehicle entry event processed successfully"
        return EventResponse(
            success=True,
            message=msg,
            journey_id=journey.id,
            current_state=journey.current_state.value,
            duplicate=is_duplicate
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/vehicle-exit", response_model=EventResponse)
def handle_vehicle_exit(payload: VehicleExitEvent, db: Session = Depends(get_db)):
    try:
        journey = journey_service.process_vehicle_exit(
            db=db,
            site_id=payload.site_id,
            camera_id=payload.camera_id,
            journey_id=payload.journey_id
        )
        return EventResponse(
            success=True,
            message="Vehicle exit event processed successfully",
            journey_id=journey.id,
            current_state=journey.current_state.value,
            duplicate=False
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
