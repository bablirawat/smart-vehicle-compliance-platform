import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class ServiceStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"

class ServiceSession(Base):
    __tablename__ = "service_sessions"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id"), nullable=False, unique=True, index=True)
    bay_id = Column(Integer, ForeignKey("bays.id"), nullable=False, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(ServiceStatus), default=ServiceStatus.IN_PROGRESS, nullable=False)

    journey = relationship("Journey", back_populates="service_session")
    bay = relationship("Bay", back_populates="sessions")
    operator = relationship("User")
