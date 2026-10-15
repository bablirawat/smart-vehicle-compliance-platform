from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.models.journeys import JourneyState

class JourneyEventOut(BaseModel):
    id: int
    journey_id: int
    vehicle_id: int
    site_id: int
    previous_state: Optional[str] = None
    new_state: str
    event_source: str
    evidence_data: Optional[str] = None
    operator_id: Optional[int] = None
    reason: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class VerificationResultOut(BaseModel):
    id: int
    verification_type: str
    source: str
    status: str
    details: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class JourneyOut(BaseModel):
    id: int
    vehicle_id: int
    vehicle_number: str
    site_id: int
    site_name: Optional[str] = None
    entry_camera_id: Optional[int] = None
    exit_camera_id: Optional[int] = None
    current_state: JourneyState
    anpr_confidence: float
    entry_time: datetime
    bay_assigned_time: Optional[datetime] = None
    service_start_time: Optional[datetime] = None
    service_end_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JourneyDetailOut(JourneyOut):
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_category: Optional[str] = None
    queue_position: Optional[int] = None
    assigned_bay_name: Optional[str] = None
    events: List[JourneyEventOut] = []
    verifications: List[VerificationResultOut] = []

class TransitionRequest(BaseModel):
    target_state: JourneyState
    reason: Optional[str] = None

class HoldReleaseRequest(BaseModel):
    reason: str

class OverrideRequest(BaseModel):
    target_state: JourneyState
    reason: str
