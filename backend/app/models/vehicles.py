from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String(50), unique=True, index=True, nullable=False)
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    category = Column(String(50), default="Commercial", nullable=False)
    owner_name = Column(String(150), nullable=True)
    compliance_status = Column(String(50), default="UNKNOWN", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    journeys = relationship("Journey", back_populates="vehicle")
