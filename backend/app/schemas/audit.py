from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    role: Optional[str] = None
    action: str
    site_id: Optional[int] = None
    site_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    previous_state: Optional[str] = None
    new_state: Optional[str] = None
    reason: Optional[str] = None
    event_type: str
    timestamp: datetime

    class Config:
        from_attributes = True
