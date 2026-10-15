from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.queues import QueueItem, QueueStatus
from app.models.journeys import Journey, JourneyState
from app.models.sites import Site
from app.services.alert_service import AlertService
from app.models.alerts import AlertSeverity
from app.websocket.connection_manager import manager
import asyncio

class QueueService:
    @staticmethod
    def enqueue(db: Session, journey: Journey, priority: int = 1) -> QueueItem:
        # Check if already queued
        existing = db.query(QueueItem).filter(
            QueueItem.journey_id == journey.id,
            QueueItem.status == QueueStatus.WAITING
        ).first()
        if existing:
            return existing

        # Calculate next position in site queue
        max_pos = db.query(QueueItem).filter(
            QueueItem.site_id == journey.site_id,
            QueueItem.status == QueueStatus.WAITING
        ).count()

        q_item = QueueItem(
            site_id=journey.site_id,
            journey_id=journey.id,
            vehicle_id=journey.vehicle_id,
            position=max_pos + 1,
            entry_time=datetime.utcnow(),
            wait_time_seconds=0,
            priority=priority,
            status=QueueStatus.WAITING
        )
        db.add(q_item)
        db.commit()
        db.refresh(q_item)

        # Check queue overload threshold against site capacity
        site = db.query(Site).filter(Site.id == journey.site_id).first()
        current_queue_len = max_pos + 1
        if site and current_queue_len >= site.max_queue_capacity:
            AlertService.create_alert(
                db=db,
                site_id=journey.site_id,
                alert_type="QUEUE_OVERLOAD",
                message=f"Site queue capacity reached ({current_queue_len}/{site.max_queue_capacity} vehicles in queue).",
                severity=AlertSeverity.HIGH,
                journey_id=journey.id
            )

        # Broadcast queue update event
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(journey.site_id, {
                    "type": "QUEUE_CHANGED",
                    "site_id": journey.site_id,
                    "journey_id": journey.id,
                    "position": q_item.position,
                    "queue_length": current_queue_len,
                    "timestamp": datetime.utcnow().isoformat()
                }))
        except Exception:
            pass

        return q_item

    @staticmethod
    def dequeue(db: Session, journey_id: int) -> Optional[QueueItem]:
        q_item = db.query(QueueItem).filter(QueueItem.journey_id == journey_id).first()
        if not q_item:
            return None

        site_id = q_item.site_id
        q_item.status = QueueStatus.ASSIGNED
        db.commit()

        # Recalculate positions for remaining waiting items
        waiting_items = db.query(QueueItem).filter(
            QueueItem.site_id == site_id,
            QueueItem.status == QueueStatus.WAITING
        ).order_by(QueueItem.entry_time.asc()).all()

        for idx, item in enumerate(waiting_items):
            item.position = idx + 1
        db.commit()

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(site_id, {
                    "type": "QUEUE_CHANGED",
                    "site_id": site_id,
                    "journey_id": journey_id,
                    "queue_length": len(waiting_items),
                    "timestamp": datetime.utcnow().isoformat()
                }))
        except Exception:
            pass

        return q_item

queue_service = QueueService()
