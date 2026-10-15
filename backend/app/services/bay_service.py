from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.bays import Bay, BayStatus
from app.models.journeys import Journey, JourneyState
from app.models.sessions import ServiceSession, ServiceStatus
from app.services.alert_service import AlertService
from app.models.alerts import AlertSeverity
from app.websocket.connection_manager import manager
import asyncio

class BayService:
    @staticmethod
    def auto_assign_bay(db: Session, journey: Journey) -> Optional[Bay]:
        # Lock site bays to prevent double assignment concurrency
        available_bay = db.query(Bay).filter(
            Bay.site_id == journey.site_id,
            Bay.status == BayStatus.AVAILABLE
        ).with_for_update(nowait=False).first()

        if not available_bay:
            # Alert no available bay
            AlertService.create_alert(
                db=db,
                site_id=journey.site_id,
                alert_type="RESOURCE_UNAVAILABLE",
                message=f"No available inspection bays for vehicle (Journey #{journey.id}).",
                severity=AlertSeverity.MEDIUM,
                journey_id=journey.id
            )
            return None

        # Assign bay to journey
        available_bay.status = BayStatus.RESERVED
        available_bay.current_journey_id = journey.id
        journey.bay_assigned_time = datetime.utcnow()
        db.commit()
        db.refresh(available_bay)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(journey.site_id, {
                    "type": "BAY_ASSIGNED",
                    "site_id": journey.site_id,
                    "journey_id": journey.id,
                    "bay_id": available_bay.id,
                    "bay_name": available_bay.bay_name,
                    "timestamp": datetime.utcnow().isoformat()
                }))
        except Exception:
            pass

        return available_bay

    @staticmethod
    def start_service(db: Session, journey: Journey, bay_id: int, operator_id: int) -> ServiceSession:
        bay = db.query(Bay).filter(Bay.id == bay_id).first()
        if not bay:
            raise ValueError(f"Bay #{bay_id} not found.")

        bay.status = BayStatus.OCCUPIED
        bay.current_journey_id = journey.id
        journey.service_start_time = datetime.utcnow()

        session = ServiceSession(
            journey_id=journey.id,
            bay_id=bay_id,
            operator_id=operator_id,
            start_time=journey.service_start_time,
            status=ServiceStatus.IN_PROGRESS
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(journey.site_id, {
                    "type": "SERVICE_STARTED",
                    "site_id": journey.site_id,
                    "journey_id": journey.id,
                    "bay_id": bay_id,
                    "operator_id": operator_id,
                    "timestamp": datetime.utcnow().isoformat()
                }))
        except Exception:
            pass

        return session

    @staticmethod
    def complete_service(db: Session, journey: Journey, notes: str = None) -> ServiceSession:
        session = db.query(ServiceSession).filter(
            ServiceSession.journey_id == journey.id,
            ServiceSession.status == ServiceStatus.IN_PROGRESS
        ).first()

        now = datetime.utcnow()
        journey.service_end_time = now

        if session:
            session.end_time = now
            session.status = ServiceStatus.COMPLETED
            if session.start_time:
                session.duration_seconds = int((now - session.start_time).total_seconds())
            if notes:
                session.notes = notes

        # Release bay
        bay = db.query(Bay).filter(Bay.current_journey_id == journey.id).first()
        if bay:
            bay.status = BayStatus.AVAILABLE
            bay.current_journey_id = None

        db.commit()

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(journey.site_id, {
                    "type": "SERVICE_COMPLETED",
                    "site_id": journey.site_id,
                    "journey_id": journey.id,
                    "bay_id": bay.id if bay else None,
                    "timestamp": datetime.utcnow().isoformat()
                }))
        except Exception:
            pass

        return session

bay_service = BayService()
