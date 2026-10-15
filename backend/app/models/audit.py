from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True, index=True)
    vehicle_number = Column(String(50), nullable=True, index=True)
    previous_state = Column(String(50), nullable=True)
    new_state = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User")
    site = relationship("Site")
