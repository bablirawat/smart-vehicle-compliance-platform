import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class BayStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    OCCUPIED = "OCCUPIED"
    BLOCKED = "BLOCKED"
    MAINTENANCE = "MAINTENANCE"

class Bay(Base):
    __tablename__ = "bays"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    bay_name = Column(String(100), nullable=False)
    bay_type = Column(String(50), default="Standard Inspection", nullable=False)
    status = Column(Enum(BayStatus), default=BayStatus.AVAILABLE, nullable=False, index=True)
    current_journey_id = Column(Integer, ForeignKey("journeys.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    site = relationship("Site", back_populates="bays")
    current_journey = relationship("Journey", foreign_keys=[current_journey_id])
    sessions = relationship("ServiceSession", back_populates="bay")
