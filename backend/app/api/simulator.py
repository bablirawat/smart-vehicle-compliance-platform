from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.simulator import SimulatorVehicleRequest, SimulatorCameraOfflineRequest, SimulatorApiFailureRequest
from app.simulator.simulator_engine import simulator_engine

router = APIRouter(prefix="/simulator", tags=["Simulator Control Panel"])

@router.post("/vehicle")
def simulate_vehicle_entry(payload: SimulatorVehicleRequest, db: Session = Depends(get_db)):
    try:
        journey, is_duplicate = simulator_engine.simulate_entry(
            db=db,
            site_id=payload.site_id,
            vehicle_type=payload.vehicle_type,
            vehicle_number=payload.vehicle_number,
            confidence=payload.confidence
        )
        return {
            "success": True,
            "journey_id": journey.id,
            "vehicle_number": journey.vehicle.vehicle_number,
            "current_state": journey.current_state.value,
            "duplicate": is_duplicate
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/camera-offline")
def simulate_camera_offline(payload: SimulatorCameraOfflineRequest, db: Session = Depends(get_db)):
    try:
        camera = simulator_engine.simulate_camera_offline(
            db=db,
            site_id=payload.site_id,
            camera_id=payload.camera_id,
            offline=payload.offline
        )
        return {
            "success": True,
            "camera_id": camera.id,
            "camera_code": camera.camera_code,
            "status": camera.status.value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/external-failure")
def simulate_external_api_failure(payload: SimulatorApiFailureRequest):
    res = simulator_engine.simulate_api_failure(
        service_name=payload.service_name,
        fail=payload.fail
    )
    return {"success": True, "details": res}
