import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.journey_service import journey_service
from app.services.verification_service import VerificationService
from app.services.alert_service import AlertService
from app.services.bay_service import BayService
from app.models.cameras import Camera, CameraStatus
from app.models.bays import Bay, BayStatus
from app.models.journeys import Journey, JourneyState
from app.models.alerts import AlertSeverity

class SimulatorEngine:
    @staticmethod
    def simulate_entry(db: Session, site_id: int, vehicle_type: str = "NORMAL", vehicle_number: str = None, confidence: float = 0.95):
        if not vehicle_number:
            rand_suffix = random.randint(1000, 9999)
            if vehicle_type == "EXPIRED":
                vehicle_number = f"DL01-EXPIRED-{rand_suffix}"
            elif vehicle_type == "INVALID_IDENTITY":
                vehicle_number = f"DL01-INVALID-{rand_suffix}"
            elif vehicle_type == "DUE_SOON":
                vehicle_number = f"DL01-DUE-{rand_suffix}"
            elif vehicle_type == "FAIL":
                vehicle_number = f"DL01-FAIL-{rand_suffix}"
            else:
                vehicle_number = f"DL01-AB-{rand_suffix}"

        camera = db.query(Camera).filter(Camera.site_id == site_id, Camera.type == "ENTRY").first()
        camera_id = camera.id if camera else 1

        conf = 0.65 if vehicle_type == "LOW_CONFIDENCE" else confidence

        journey, is_dup = journey_service.process_vehicle_entry(
            db=db,
            site_id=site_id,
            camera_id=camera_id,
            vehicle_number=vehicle_number,
            confidence=conf
        )
        return journey, is_dup

    @staticmethod
    def simulate_camera_offline(db: Session, site_id: int, camera_id: int, offline: bool = True):
        camera = db.query(Camera).filter(Camera.id == camera_id).first()
        if not camera:
            raise ValueError(f"Camera #{camera_id} not found.")

        camera.status = CameraStatus.OFFLINE if offline else CameraStatus.ONLINE
        db.commit()

        if offline:
            AlertService.create_alert(
                db=db,
                site_id=site_id,
                alert_type="CAMERA_OFFLINE",
                message=f"ANPR Camera '{camera.camera_code}' went OFFLINE.",
                severity=AlertSeverity.HIGH
            )
        return camera

    @staticmethod
    def simulate_api_failure(service_name: str, fail: bool):
        VerificationService.set_forced_failure(service_name, fail)
        return {"service": service_name, "failure_simulated": fail}

simulator_engine = SimulatorEngine()
