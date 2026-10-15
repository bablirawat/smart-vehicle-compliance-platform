import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class QueueStatus(str, enum.Enum):
    WAITING = "WAITING"
    ASSIGNED = "ASSIGNED"
    REMOVED = "REMOVED"

class QueueItem(Base):
    __tablename__ = "queues"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id"), nullable=False, unique=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    position = Column(Integer, nullable=False)
    entry_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    wait_time_seconds = Column(Integer, default=0, nullable=False)
    priority = Column(Integer, default=1, nullable=False) # 1=Normal, 2=High
    status = Column(Enum(QueueStatus), default=QueueStatus.WAITING, nullable=False)

    site = relationship("Site", back_populates="queues")
    journey = relationship("Journey", back_populates="queue_item")
    vehicle = relationship("Vehicle")
