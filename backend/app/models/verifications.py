import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class VerificationType(str, enum.Enum):
    IDENTITY = "IDENTITY"
    COMPLIANCE = "COMPLIANCE"

class VerificationStatus(str, enum.Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    UNAVAILABLE = "UNAVAILABLE"

class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True)
    journey_id = Column(Integer, ForeignKey("journeys.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    verification_type = Column(Enum(VerificationType), nullable=False)
    source = Column(String(100), nullable=False) # e.g. National_Reg_DB, Govt_Compliance_Portal
    status = Column(Enum(VerificationStatus), nullable=False)
    details = Column(Text, nullable=True) # Details JSON or payload summary
    error_message = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    journey = relationship("Journey", back_populates="verifications")
