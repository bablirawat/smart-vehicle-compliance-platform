from typing import Optional
from pydantic import BaseModel

class SimulatorVehicleRequest(BaseModel):
    site_id: int
    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = "COMMERCIAL" # NORMAL, EXPIRED, DUE_SOON, INVALID_IDENTITY, LOW_CONFIDENCE
    confidence: Optional[float] = 0.95

class SimulatorCameraOfflineRequest(BaseModel):
    site_id: int
    camera_id: int
    offline: bool = True

class SimulatorApiFailureRequest(BaseModel):
    service_name: str # IDENTITY or COMPLIANCE
    fail: bool = True
