import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class SiteStatus(str, enum.Enum):
    ONLINE = "ONLINE"
    WARNING = "WARNING"
    OFFLINE = "OFFLINE"

class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    location = Column(String(255), nullable=False)
    status = Column(Enum(SiteStatus), default=SiteStatus.ONLINE, nullable=False)
    max_queue_capacity = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="site")
    cameras = relationship("Camera", back_populates="site")
    journeys = relationship("Journey", back_populates="site")
    queues = relationship("QueueItem", back_populates="site")
    bays = relationship("Bay", back_populates="site")
    alerts = relationship("Alert", back_populates="site")
