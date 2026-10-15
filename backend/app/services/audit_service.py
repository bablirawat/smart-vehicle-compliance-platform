from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.users import User

class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        event_type: str,
        user: Optional[User] = None,
        site_id: Optional[int] = None,
        vehicle_number: Optional[str] = None,
        previous_state: Optional[str] = None,
        new_state: Optional[str] = None,
        reason: Optional[str] = None
    ) -> AuditLog:
        audit = AuditLog(
            user_id=user.id if user else None,
            user_email=user.email if user else "SYSTEM",
            role=user.role.value if user else "SYSTEM",
            action=action,
            site_id=site_id or (user.site_id if user else None),
            vehicle_number=vehicle_number,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason,
            event_type=event_type,
            timestamp=datetime.utcnow()
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        return audit

audit_service = AuditService()
