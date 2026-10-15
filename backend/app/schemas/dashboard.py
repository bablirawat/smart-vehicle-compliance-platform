from typing import Optional, List
from pydantic import BaseModel

class KPIMetrics(BaseModel):
    current_vehicles: int
    queue_length: int
    available_bays: int
    occupied_bays: int
    verification_pending: int
    open_alerts: int
    avg_wait_time_minutes: float
    avg_service_time_minutes: float
    avg_turnaround_time_minutes: float
    throughput_per_hour: float
    resource_utilization_percent: float
    eligibility_rate_percent: float
    alert_rate_percent: float

class SiteSummary(BaseModel):
    site_id: int
    site_name: str
    site_code: str
    status: str
    location: str
    active_vehicles: int
    queue_length: int
    open_alerts: int
    total_bays: int
    occupied_bays: int
    resource_utilization: float

class CentralCommandDashboardData(BaseModel):
    total_sites: int
    online_sites: int
    sites_with_alerts: int
    total_active_vehicles: int
    network_queue_length: int
    avg_network_wait_time_minutes: float
    avg_network_turnaround_time_minutes: float
    network_resource_utilization_percent: float
    network_throughput_per_hour: float
    network_eligibility_rate_percent: float
    critical_alerts_count: int
    site_summaries: List[SiteSummary]
