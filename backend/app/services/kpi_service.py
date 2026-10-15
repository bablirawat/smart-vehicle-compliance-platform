from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.journeys import Journey, JourneyState
from app.models.queues import QueueItem, QueueStatus
from app.models.bays import Bay, BayStatus
from app.models.alerts import Alert, AlertStatus, AlertSeverity
from app.models.verifications import VerificationResult, VerificationStatus
from app.schemas.dashboard import KPIMetrics

class KPIService:
    @staticmethod
    def calculate_site_kpis(db: Session, site_id: Optional[int] = None, timeframe: str = "TODAY") -> KPIMetrics:
        now = datetime.utcnow()
        if timeframe == "LAST 24 HOURS":
            start_time = now - timedelta(hours=24)
        elif timeframe == "LAST 7 DAYS":
            start_time = now - timedelta(days=7)
        else: # TODAY
            start_time = datetime(now.year, now.month, now.day)

        journey_query = db.query(Journey)
        if site_id:
            journey_query = journey_query.filter(Journey.site_id == site_id)

        # Active vehicles currently on site (not EXITED)
        active_vehicles = journey_query.filter(
            Journey.entry_time >= start_time,
            Journey.current_state != JourneyState.EXITED
        ).count()

        # Queue length
        q_query = db.query(QueueItem).filter(QueueItem.status == QueueStatus.WAITING)
        if site_id:
            q_query = q_query.filter(QueueItem.site_id == site_id)
        queue_length = q_query.count()

        # Bays metrics
        bays_query = db.query(Bay)
        if site_id:
            bays_query = bays_query.filter(Bay.site_id == site_id)
        total_bays = bays_query.count()
        available_bays = bays_query.filter(Bay.status == BayStatus.AVAILABLE).count()
        occupied_bays = bays_query.filter(Bay.status.in_([BayStatus.OCCUPIED, BayStatus.RESERVED])).count()
        resource_utilization = (occupied_bays / total_bays * 100.0) if total_bays > 0 else 0.0

        # Verification pending
        verification_pending = journey_query.filter(
            Journey.entry_time >= start_time,
            Journey.current_state.in_([JourneyState.ENTERED, JourneyState.IDENTIFIED])
        ).count()

        # Open alerts
        alert_query = db.query(Alert).filter(Alert.status == AlertStatus.OPEN)
        if site_id:
            alert_query = alert_query.filter(Alert.site_id == site_id)
        open_alerts = alert_query.count()

        # Average Wait Time (Bay Assignment Time - Entry Time in minutes)
        wait_times_query = journey_query.filter(
            Journey.entry_time >= start_time,
            Journey.bay_assigned_time.isnot(None)
        ).all()
        wait_durations = [(j.bay_assigned_time - j.entry_time).total_seconds() / 60.0 for j in wait_times_query if j.bay_assigned_time]
        avg_wait = (sum(wait_durations) / len(wait_durations)) if wait_durations else 0.0

        # Average Service Time (Service End Time - Service Start Time in minutes)
        service_times_query = journey_query.filter(
            Journey.entry_time >= start_time,
            Journey.service_start_time.isnot(None),
            Journey.service_end_time.isnot(None)
        ).all()
        service_durations = [(j.service_end_time - j.service_start_time).total_seconds() / 60.0 for j in service_times_query]
        avg_service = (sum(service_durations) / len(service_durations)) if service_durations else 0.0

        # Average Turnaround Time (Exit Time - Entry Time in minutes)
        completed_journeys = journey_query.filter(
            Journey.entry_time >= start_time,
            Journey.current_state == JourneyState.EXITED,
            Journey.exit_time.isnot(None)
        ).all()
        turnaround_durations = [(j.exit_time - j.entry_time).total_seconds() / 60.0 for j in completed_journeys]
        avg_turnaround = (sum(turnaround_durations) / len(turnaround_durations)) if turnaround_durations else 0.0

        # Throughput per hour
        hours_elapsed = max(1.0, (now - start_time).total_seconds() / 3600.0)
        throughput = len(completed_journeys) / hours_elapsed

        # Eligibility rate %
        verified_count = journey_query.filter(
            Journey.entry_time >= start_time,
            Journey.current_state.notin_([JourneyState.ENTERED, JourneyState.IDENTIFIED])
        ).count()
        eligible_count = journey_query.filter(
            Journey.entry_time >= start_time,
            Journey.current_state.in_([JourneyState.ELIGIBLE, JourneyState.QUEUED, JourneyState.BAY_ASSIGNED, JourneyState.IN_SERVICE, JourneyState.SERVICE_COMPLETED, JourneyState.EXITED])
        ).count()
        eligibility_rate = (eligible_count / verified_count * 100.0) if verified_count > 0 else 100.0

        # Alert rate %
        total_journeys_period = journey_query.filter(Journey.entry_time >= start_time).count()
        alerting_journeys = journey_query.filter(
            Journey.entry_time >= start_time,
            Journey.alerts.any()
        ).count()
        alert_rate = (alerting_journeys / total_journeys_period * 100.0) if total_journeys_period > 0 else 0.0

        return KPIMetrics(
            current_vehicles=active_vehicles,
            queue_length=queue_length,
            available_bays=available_bays,
            occupied_bays=occupied_bays,
            verification_pending=verification_pending,
            open_alerts=open_alerts,
            avg_wait_time_minutes=round(avg_wait, 2),
            avg_service_time_minutes=round(avg_service, 2),
            avg_turnaround_time_minutes=round(avg_turnaround, 2),
            throughput_per_hour=round(throughput, 2),
            resource_utilization_percent=round(resource_utilization, 2),
            eligibility_rate_percent=round(eligibility_rate, 2),
            alert_rate_percent=round(alert_rate, 2)
        )

kpi_service = KPIService()
