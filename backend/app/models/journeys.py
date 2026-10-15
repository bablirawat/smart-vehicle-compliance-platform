import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base

class JourneyState(str, enum.Enum):
    ENTERED = "ENTERED"
    IDENTIFIED = "IDENTIFIED"
    VERIFIED = "VERIFIED"
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    QUEUED = "QUEUED"
    BAY_ASSIGNED = "BAY_ASSIGNED"
    IN_SERVICE = "IN_SERVICE"
    SERVICE_COMPLETED = "SERVICE_COMPLETED"
    EXITED = "EXITED"
    HOLD = "HOLD"

class Journey(Base):
    __tablename__ = "journeys"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    entry_camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    exit_camera_id = Column(Integer, ForeignKey("cameras.id"), nullable=True)
    current_state = Column(Enum(JourneyState), default=JourneyState.ENTERED, nullable=False, index=True)
    anpr_confidence = Column(Float, default=1.0, nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    bay_assigned_time = Column(DateTime, nullable=True)
    service_start_time = Column(DateTime, nullable=True)
    service_end_time = Column(DateTime, nullable=True)
    exit_time = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    vehicle = relationship("Vehicle", back_populates="journeys")
    site = relationship("Site", back_populates="journeys")
    events = relationship("JourneyEvent", back_populates="journey", cascade="all, delete-orphan")
    verifications = relationship("VerificationResult", back_populates="journey", cascade="all, delete-orphan")
    queue_item = relationship("QueueItem", back_populates="journey", uselist=False)
    service_session = relationship("ServiceSession", back_populates="journey", uselist=False)
    alerts = relationship("Alert", back_populates="journey")
