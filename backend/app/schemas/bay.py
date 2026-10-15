from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class BayOut(BaseModel):
    id: int
    site_id: int
    bay_name: str
    bay_type: str
    status: str
    current_journey_id: Optional[int] = None
    current_vehicle_number: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class BayAssignRequest(BaseModel):
    journey_id: int

class BayStatusUpdateRequest(BaseModel):
    status: str # MAINTENANCE, BLOCKED, AVAILABLE
    reason: Optional[str] = None
