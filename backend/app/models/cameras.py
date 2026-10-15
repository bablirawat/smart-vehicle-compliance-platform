import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class CameraType(str, enum.Enum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"

class CameraStatus(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False, index=True)
    camera_code = Column(String(50), unique=True, index=True, nullable=False)
    type = Column(Enum(CameraType), nullable=False)
    status = Column(Enum(CameraStatus), default=CameraStatus.ONLINE, nullable=False)
    last_detected_vehicle = Column(String(50), nullable=True)
    last_event_at = Column(DateTime, nullable=True)

    site = relationship("Site", back_populates="cameras")
