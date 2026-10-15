from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class AlertOut(BaseModel):
    id: int
    site_id: int
    site_name: Optional[str] = None
    journey_id: Optional[int] = None
    vehicle_number: Optional[str] = None
    alert_type: str
    severity: str
    message: str
    status: str
    acknowledged_by: Optional[int] = None
    acknowledged_by_name: Optional[str] = None
    resolved_by: Optional[int] = None
    resolved_by_name: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AlertActionRequest(BaseModel):
    notes: Optional[str] = None
