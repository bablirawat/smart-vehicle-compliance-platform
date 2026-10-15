from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sites import Site, SiteStatus
from app.models.alerts import Alert, AlertStatus, AlertSeverity
from app.models.journeys import Journey, JourneyState
from app.models.queues import QueueItem, QueueStatus
from app.models.bays import Bay, BayStatus
from app.models.users import User, UserRole
from app.auth.rbac import get_current_user
from app.schemas.dashboard import KPIMetrics, CentralCommandDashboardData, SiteSummary
from app.services.kpi_service import kpi_service

router = APIRouter(prefix="/dashboard", tags=["Dashboards & KPI Calculations"])

@router.get("/kpis", response_model=KPIMetrics)
def get_dashboard_kpis(
    site_id: Optional[int] = None,
    timeframe: str = Query("TODAY", description="TODAY, LAST 24 HOURS, or LAST 7 DAYS"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_site = site_id
    if current_user.role in [UserRole.OPERATOR, UserRole.SITE_MANAGER] and current_user.site_id:
        target_site = current_user.site_id

    return kpi_service.calculate_site_kpis(db, site_id=target_site, timeframe=timeframe)

@router.get("/central", response_model=CentralCommandDashboardData)
def get_central_command_dashboard(
    timeframe: str = Query("TODAY"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sites = db.query(Site).all()
    total_sites = len(sites)
    online_sites = len([s for s in sites if s.status == SiteStatus.ONLINE])

    site_summaries = []
    total_active_v = 0
    total_q_len = 0
    total_critical_alerts = 0

    for site in sites:
        active_v = db.query(Journey).filter(Journey.site_id == site.id, Journey.current_state != JourneyState.EXITED).count()
        q_len = db.query(QueueItem).filter(QueueItem.site_id == site.id, QueueItem.status == QueueStatus.WAITING).count()
        open_a = db.query(Alert).filter(Alert.site_id == site.id, Alert.status == AlertStatus.OPEN).count()
        crit_a = db.query(Alert).filter(Alert.site_id == site.id, Alert.status == AlertStatus.OPEN, Alert.severity == AlertSeverity.CRITICAL).count()

        total_bays = db.query(Bay).filter(Bay.site_id == site.id).count()
        occ_bays = db.query(Bay).filter(Bay.site_id == site.id, Bay.status.in_([BayStatus.OCCUPIED, BayStatus.RESERVED])).count()
        utilization = (occ_bays / total_bays * 100.0) if total_bays > 0 else 0.0

        total_active_v += active_v
        total_q_len += q_len
        total_critical_alerts += crit_a

        site_summaries.append(SiteSummary(
            site_id=site.id,
            site_name=site.name,
            site_code=site.code,
            status=site.status.value,
            location=site.location,
            active_vehicles=active_v,
            queue_length=q_len,
            open_alerts=open_a,
            total_bays=total_bays,
            occupied_bays=occ_bays,
            resource_utilization=round(utilization, 1)
        ))

    network_kpis = kpi_service.calculate_site_kpis(db, site_id=None, timeframe=timeframe)

    sites_with_alerts_count = len([s for s in site_summaries if s.open_alerts > 0])

    return CentralCommandDashboardData(
        total_sites=total_sites,
        online_sites=online_sites,
        sites_with_alerts=sites_with_alerts_count,
        total_active_vehicles=total_active_v,
        network_queue_length=total_q_len,
        avg_network_wait_time_minutes=network_kpis.avg_wait_time_minutes,
        avg_network_turnaround_time_minutes=network_kpis.avg_turnaround_time_minutes,
        network_resource_utilization_percent=network_kpis.resource_utilization_percent,
        network_throughput_per_hour=network_kpis.throughput_per_hour,
        network_eligibility_rate_percent=network_kpis.eligibility_rate_percent,
        critical_alerts_count=total_critical_alerts,
        site_summaries=site_summaries
    )
