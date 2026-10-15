from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class QueueItemOut(BaseModel):
    id: int
    site_id: int
    journey_id: int
    vehicle_id: int
    vehicle_number: str
    position: int
    entry_time: datetime
    wait_time_seconds: int
    priority: int
    status: str
    eligibility_status: Optional[str] = "ELIGIBLE"

    class Config:
        from_attributes = True
