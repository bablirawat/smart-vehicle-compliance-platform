from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.models.vehicles import Vehicle
from app.models.journeys import Journey, JourneyState
from app.models.events import JourneyEvent
from app.models.sites import Site
from app.models.cameras import Camera, CameraStatus
from app.models.users import User
from app.models.alerts import AlertSeverity
from app.state_machine.journey_state_machine import JourneyStateMachine, InvalidStateTransitionException
from app.services.verification_service import VerificationService
from app.rules.eligibility_engine import EligibilityEngine
from app.services.queue_service import QueueService
from app.services.bay_service import BayService
from app.services.alert_service import AlertService
from app.services.audit_service import AuditService
from app.websocket.connection_manager import manager
import asyncio
import json

class JourneyService:
    @staticmethod
    def process_vehicle_entry(
        db: Session,
        site_id: int,
        camera_id: int,
        vehicle_number: str,
        confidence: float,
        timestamp: Optional[datetime] = None
    ) -> Tuple[Journey, bool]: # returns (journey, is_duplicate)
        timestamp = timestamp or datetime.utcnow()
        v_number = vehicle_number.strip().upper()

        # 1. Deduplication check
        window_start = timestamp - timedelta(seconds=settings.DEDUPLICATION_WINDOW_SECONDS)
        existing_journey = db.query(Journey).join(Vehicle).filter(
            Journey.site_id == site_id,
            Vehicle.vehicle_number == v_number,
            Journey.entry_time >= window_start,
            Journey.current_state != JourneyState.EXITED
        ).first()

        if existing_journey:
            # Duplicate entry detected, do not spawn duplicate journey
            AuditService.log(
                db=db,
                action="DUPLICATE_ENTRY_SUPPRESSED",
                event_type="DUPLICATE_ENTRY",
                site_id=site_id,
                vehicle_number=v_number,
                reason=f"Identical vehicle entry suppressed within deduplication window ({settings.DEDUPLICATION_WINDOW_SECONDS}s)."
            )
            return existing_journey, True

        # 2. Validate site and camera
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError(f"Site #{site_id} not found.")

        camera = db.query(Camera).filter(Camera.id == camera_id).first()
        if camera:
            camera.last_detected_vehicle = v_number
            camera.last_event_at = timestamp

        # 3. Create or update Vehicle record
        vehicle = db.query(Vehicle).filter(Vehicle.vehicle_number == v_number).first()
        if not vehicle:
            vehicle = Vehicle(
                vehicle_number=v_number,
                make="Freightliner" if "TRUCK" in v_number else "Volvo",
                model="Heavy Duty 500" if "TRUCK" in v_number else "FH16",
                year=2023,
                category="Commercial Cargo",
                owner_name=f"Owner of {v_number}",
                compliance_status="PENDING"
            )
            db.add(vehicle)
            db.commit()
            db.refresh(vehicle)

        # 4. Create new Journey
        journey = Journey(
            vehicle_id=vehicle.id,
            site_id=site_id,
            entry_camera_id=camera_id,
            current_state=JourneyState.ENTERED,
            anpr_confidence=confidence,
            entry_time=timestamp
        )
        db.add(journey)
        db.commit()
        db.refresh(journey)

        # Record ENTERED event
        event_entered = JourneyEvent(
            journey_id=journey.id,
            vehicle_id=vehicle.id,
            site_id=site_id,
            previous_state=None,
            new_state=JourneyState.ENTERED.value,
            event_source="ANPR_ENTRY_CAMERA",
            evidence_data=json.dumps({"confidence": confidence, "camera_id": camera_id}),
            timestamp=timestamp
        )
        db.add(event_entered)

        # Low confidence handling
        if confidence < settings.ANPR_CONFIDENCE_THRESHOLD:
            AlertService.create_alert(
                db=db,
                site_id=site_id,
                alert_type="LOW_ANPR_CONFIDENCE",
                message=f"Low ANPR confidence ({confidence * 100:.1f}%) detected for vehicle {v_number}. Needs operator verification.",
                severity=AlertSeverity.MEDIUM,
                journey_id=journey.id
            )

        # Auto transition ENTERED -> IDENTIFIED
        JourneyStateMachine.validate_transition(journey.current_state, JourneyState.IDENTIFIED)
        journey.current_state = JourneyState.IDENTIFIED
        
        event_identified = JourneyEvent(
            journey_id=journey.id,
            vehicle_id=vehicle.id,
            site_id=site_id,
            previous_state=JourneyState.ENTERED.value,
            new_state=JourneyState.IDENTIFIED.value,
            event_source="SYSTEM_IDENTIFIER",
            timestamp=datetime.utcnow()
        )
        db.add(event_identified)
        db.commit()

        # Auto transition IDENTIFIED -> VERIFIED via verification services
        v_ident = VerificationService.verify_identity(db, journey.id, vehicle)
        v_comp = VerificationService.verify_compliance(db, journey.id, vehicle)

        journey.current_state = JourneyState.VERIFIED
        event_verified = JourneyEvent(
            journey_id=journey.id,
            vehicle_id=vehicle.id,
            site_id=site_id,
            previous_state=JourneyState.IDENTIFIED.value,
            new_state=JourneyState.VERIFIED.value,
            event_source="EXTERNAL_VERIFICATION_SERVICES",
            evidence_data=json.dumps({
                "identity": v_ident.status.value,
                "compliance": v_comp.status.value
            }),
            timestamp=datetime.utcnow()
        )
        db.add(event_verified)
        db.commit()

        # Evaluate Eligibility Engine
        verifications = [v_ident, v_comp]
        decision = EligibilityEngine.evaluate(verifications)

        if decision.is_eligible:
            journey.current_state = JourneyState.ELIGIBLE
            vehicle.compliance_status = "ELIGIBLE"
            
            event_elig = JourneyEvent(
                journey_id=journey.id,
                vehicle_id=vehicle.id,
                site_id=site_id,
                previous_state=JourneyState.VERIFIED.value,
                new_state=JourneyState.ELIGIBLE.value,
                event_source="ELIGIBILITY_ENGINE",
                evidence_data=json.dumps({"code": decision.code, "message": decision.message}),
                timestamp=datetime.utcnow()
            )
            db.add(event_elig)
            db.commit()

            # Enqueue vehicle automatically
            QueueService.enqueue(db, journey)
            journey.current_state = JourneyState.QUEUED
            
            event_queued = JourneyEvent(
                journey_id=journey.id,
                vehicle_id=vehicle.id,
                site_id=site_id,
                previous_state=JourneyState.ELIGIBLE.value,
                new_state=JourneyState.QUEUED.value,
                event_source="QUEUE_MANAGER",
                timestamp=datetime.utcnow()
            )
            db.add(event_queued)
            db.commit()

            # Attempt auto bay assignment if available
            bay = BayService.auto_assign_bay(db, journey)
            if bay:
                journey.current_state = JourneyState.BAY_ASSIGNED
                QueueService.dequeue(db, journey.id)
                event_bay = JourneyEvent(
                    journey_id=journey.id,
                    vehicle_id=vehicle.id,
                    site_id=site_id,
                    previous_state=JourneyState.QUEUED.value,
                    new_state=JourneyState.BAY_ASSIGNED.value,
                    event_source="BAY_AUTO_ASSIGNER",
                    evidence_data=json.dumps({"bay_id": bay.id, "bay_name": bay.bay_name}),
                    timestamp=datetime.utcnow()
                )
                db.add(event_bay)
                db.commit()

        else:
            # Vehicle Not Eligible or Fails Verification -> Move to HOLD
            journey.current_state = JourneyState.HOLD
            vehicle.compliance_status = "NON_COMPLIANT"

            event_hold = JourneyEvent(
                journey_id=journey.id,
                vehicle_id=vehicle.id,
                site_id=site_id,
                previous_state=JourneyState.VERIFIED.value,
                new_state=JourneyState.HOLD.value,
                event_source="ELIGIBILITY_ENGINE",
                evidence_data=json.dumps({"code": decision.code, "message": decision.message}),
                reason=decision.message,
                timestamp=datetime.utcnow()
            )
            db.add(event_hold)

            # Create High Severity Alert
            AlertService.create_alert(
                db=db,
                site_id=site_id,
                alert_type="NON_ELIGIBLE_VEHICLE",
                message=f"Vehicle {v_number} failed eligibility verification: {decision.message}",
                severity=AlertSeverity.HIGH if decision.code != "SOURCE_UNAVAILABLE" else AlertSeverity.MEDIUM,
                journey_id=journey.id
            )
            db.commit()

        # Broadcast real-time entry notification
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(site_id, {
                    "type": "VEHICLE_ENTERED",
                    "site_id": site_id,
                    "journey_id": journey.id,
                    "vehicle_number": v_number,
                    "current_state": journey.current_state.value,
                    "timestamp": journey.entry_time.isoformat()
                }))
        except Exception:
            pass

        return journey, False

    @staticmethod
    def transition_state(
        db: Session,
        journey_id: int,
        target_state: JourneyState,
        user: Optional[User] = None,
        reason: Optional[str] = None,
        is_override: bool = False
    ) -> Journey:
        journey = db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey:
            raise ValueError(f"Journey #{journey_id} not found.")

        current = journey.current_state

        # Validate transition using backend state machine
        JourneyStateMachine.validate_transition(current, target_state, is_override=is_override)

        journey.current_state = target_state
        journey.updated_at = datetime.utcnow()

        event = JourneyEvent(
            journey_id=journey.id,
            vehicle_id=journey.vehicle_id,
            site_id=journey.site_id,
            previous_state=current.value if isinstance(current, JourneyState) else str(current),
            new_state=target_state.value if isinstance(target_state, JourneyState) else str(target_state),
            event_source=f"USER_{user.role.value}" if user else "SYSTEM",
            operator_id=user.id if user else None,
            reason=reason,
            timestamp=datetime.utcnow()
        )
        db.add(event)
        db.commit()
        db.refresh(journey)

        # Audit log if operator action
        if user:
            AuditService.log(
                db=db,
                action="STATE_TRANSITION" if not is_override else "OPERATOR_OVERRIDE",
                event_type="STATE_CHANGE",
                user=user,
                site_id=journey.site_id,
                vehicle_number=journey.vehicle.vehicle_number if journey.vehicle else None,
                previous_state=current.value,
                new_state=target_state.value,
                reason=reason
            )

        # Broadcast WebSocket event
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(journey.site_id, {
                    "type": "STATE_CHANGED",
                    "site_id": journey.site_id,
                    "journey_id": journey.id,
                    "previous_state": current.value,
                    "new_state": target_state.value,
                    "timestamp": datetime.utcnow().isoformat()
                }))
        except Exception:
            pass

        return journey

    @staticmethod
    def process_vehicle_exit(db: Session, site_id: int, camera_id: int, journey_id: int, user: Optional[User] = None) -> Journey:
        journey = db.query(Journey).filter(Journey.id == journey_id, Journey.site_id == site_id).first()
        if not journey:
            raise ValueError(f"Active journey #{journey_id} not found at site #{site_id}.")

        # Can only exit from SERVICE_COMPLETED or HOLD state
        if journey.current_state not in [JourneyState.SERVICE_COMPLETED, JourneyState.HOLD]:
            raise InvalidStateTransitionException(
                current_state=journey.current_state.value,
                target_state=JourneyState.EXITED.value,
                reason="Vehicle cannot exit before completing service or being released from HOLD."
            )

        now = datetime.utcnow()
        journey.exit_camera_id = camera_id
        journey.exit_time = now
        journey.current_state = JourneyState.EXITED
        journey.updated_at = now

        # Update exit camera timestamp
        camera = db.query(Camera).filter(Camera.id == camera_id).first()
        if camera:
            camera.last_detected_vehicle = journey.vehicle.vehicle_number if journey.vehicle else None
            camera.last_event_at = now

        # Release queue or bay resources if any remain
        QueueService.dequeue(db, journey.id)
        
        event = JourneyEvent(
            journey_id=journey.id,
            vehicle_id=journey.vehicle_id,
            site_id=journey.site_id,
            previous_state=JourneyState.SERVICE_COMPLETED.value,
            new_state=JourneyState.EXITED.value,
            event_source="ANPR_EXIT_CAMERA",
            operator_id=user.id if user else None,
            timestamp=now
        )
        db.add(event)
        db.commit()

        AuditService.log(
            db=db,
            action="VEHICLE_EXITED",
            event_type="VEHICLE_EXIT",
            user=user,
            site_id=journey.site_id,
            vehicle_number=journey.vehicle.vehicle_number if journey.vehicle else None,
            previous_state=JourneyState.SERVICE_COMPLETED.value,
            new_state=JourneyState.EXITED.value
        )

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(site_id, {
                    "type": "VEHICLE_EXITED",
                    "site_id": site_id,
                    "journey_id": journey.id,
                    "vehicle_number": journey.vehicle.vehicle_number if journey.vehicle else "",
                    "timestamp": now.isoformat()
                }))
        except Exception:
            pass

        return journey

journey_service = JourneyService()
