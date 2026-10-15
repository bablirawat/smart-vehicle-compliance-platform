from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.alerts import Alert, AlertSeverity, AlertStatus
from app.models.users import User
from app.models.sites import Site, SiteStatus
from app.websocket.connection_manager import manager
import asyncio

class AlertService:
    @staticmethod
    def create_alert(
        db: Session,
        site_id: int,
        alert_type: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        journey_id: Optional[int] = None
    ) -> Alert:
        alert = Alert(
            site_id=site_id,
            journey_id=journey_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            status=AlertStatus.OPEN,
            created_at=datetime.utcnow()
        )
        db.add(alert)
        
        # If critical or camera offline, update site status
        if severity == AlertSeverity.CRITICAL or alert_type == "CAMERA_OFFLINE":
            site = db.query(Site).filter(Site.id == site_id).first()
            if site:
                site.status = SiteStatus.WARNING if severity != AlertSeverity.CRITICAL else SiteStatus.OFFLINE
        
        db.commit()
        db.refresh(alert)

        # Broadcast real-time alert event
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(site_id, {
                    "type": "ALERT_CREATED",
                    "site_id": site_id,
                    "alert_id": alert.id,
                    "alert_type": alert_type,
                    "severity": severity.value,
                    "message": message,
                    "timestamp": alert.created_at.isoformat()
                }))
        except Exception:
            pass

        return alert

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int, user: User) -> Alert:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert with ID {alert_id} not found.")
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = user.id
        db.commit()
        db.refresh(alert)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(alert.site_id, {
                    "type": "ALERT_ACKNOWLEDGED",
                    "site_id": alert.site_id,
                    "alert_id": alert.id,
                    "acknowledged_by": user.email,
                    "timestamp": datetime.utcnow().isoformat()
                }))
        except Exception:
            pass

        return alert

    @staticmethod
    def resolve_alert(db: Session, alert_id: int, user: User, notes: str = None) -> Alert:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert with ID {alert_id} not found.")
        alert.status = AlertStatus.RESOLVED
        alert.resolved_by = user.id
        alert.resolved_at = datetime.utcnow()
        
        # Check if open alerts remaining for site
        open_count = db.query(Alert).filter(Alert.site_id == alert.site_id, Alert.status == AlertStatus.OPEN).count()
        if open_count <= 1:
            site = db.query(Site).filter(Site.id == alert.site_id).first()
            if site and site.status != SiteStatus.ONLINE:
                site.status = SiteStatus.ONLINE

        db.commit()
        db.refresh(alert)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast_to_site(alert.site_id, {
                    "type": "ALERT_RESOLVED",
                    "site_id": alert.site_id,
                    "alert_id": alert.id,
                    "resolved_by": user.email,
                    "timestamp": datetime.utcnow().isoformat()
                }))
        except Exception:
            pass

        return alert

alert_service = AlertService()
