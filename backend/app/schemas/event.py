from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class VehicleEntryEvent(BaseModel):
    site_id: int
    camera_id: int
    vehicle_number: str
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    timestamp: Optional[datetime] = None

class VehicleExitEvent(BaseModel):
    site_id: int
    camera_id: int
    journey_id: int
    timestamp: Optional[datetime] = None

class EventResponse(BaseModel):
    success: bool
    message: str
    journey_id: Optional[int] = None
    current_state: Optional[str] = None
    duplicate: bool = False
