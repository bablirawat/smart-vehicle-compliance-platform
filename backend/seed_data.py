import logging
from datetime import datetime, timedelta
from app.database import SessionLocal, Base, engine
import app.models  # Register models
from app.models.users import User, UserRole
from app.models.sites import Site, SiteStatus
from app.models.cameras import Camera, CameraType, CameraStatus
from app.models.bays import Bay, BayStatus
from app.models.vehicles import Vehicle
from app.models.journeys import Journey, JourneyState
from app.models.events import JourneyEvent
from app.models.verifications import VerificationResult, VerificationType, VerificationStatus
from app.models.alerts import Alert, AlertSeverity, AlertStatus
from app.auth.passwords import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_data")


def populate_demo_data(db):
    """Populate demo sites, cameras, bays, RBAC users, vehicles, and initial journeys idempotently in a single transaction."""
    # 1. Create or get Sites
    sites_data = [
        {"name": "North Terminal Logistics Hub", "code": "SITE-A", "location": "Delhi NCR Hub", "status": SiteStatus.ONLINE, "max_queue_capacity": 10},
        {"name": "East Coast Cargo Station", "code": "SITE-B", "location": "Mumbai Port Terminal", "status": SiteStatus.ONLINE, "max_queue_capacity": 8},
        {"name": "South Freight Transit Hub", "code": "SITE-C", "location": "Bengaluru Outer Ring", "status": SiteStatus.ONLINE, "max_queue_capacity": 12},
    ]
    sites = {}
    for s_data in sites_data:
        site = db.query(Site).filter_by(code=s_data["code"]).first()
        if not site:
            site = Site(**s_data)
            db.add(site)
            db.flush()
        sites[s_data["code"]] = site

    site_a = sites["SITE-A"]
    site_b = sites["SITE-B"]
    site_c = sites["SITE-C"]

    # 2. Create or get Cameras
    cams_data = [
        {"site_id": site_a.id, "camera_code": "CAM-A-ENTRY-01", "type": CameraType.ENTRY, "status": CameraStatus.ONLINE},
        {"site_id": site_a.id, "camera_code": "CAM-A-EXIT-01", "type": CameraType.EXIT, "status": CameraStatus.ONLINE},
        {"site_id": site_b.id, "camera_code": "CAM-B-ENTRY-01", "type": CameraType.ENTRY, "status": CameraStatus.ONLINE},
        {"site_id": site_b.id, "camera_code": "CAM-B-EXIT-01", "type": CameraType.EXIT, "status": CameraStatus.ONLINE},
        {"site_id": site_c.id, "camera_code": "CAM-C-ENTRY-01", "type": CameraType.ENTRY, "status": CameraStatus.ONLINE},
        {"site_id": site_c.id, "camera_code": "CAM-C-EXIT-01", "type": CameraType.EXIT, "status": CameraStatus.ONLINE},
    ]
    cameras = {}
    for c_data in cams_data:
        cam = db.query(Camera).filter_by(camera_code=c_data["camera_code"]).first()
        if not cam:
            cam = Camera(**c_data)
            db.add(cam)
            db.flush()
        cameras[c_data["camera_code"]] = cam

    cam_a_in = cameras["CAM-A-ENTRY-01"]
    cam_a_out = cameras["CAM-A-EXIT-01"]
    cam_b_in = cameras["CAM-B-ENTRY-01"]
    cam_b_out = cameras["CAM-B-EXIT-01"]

    # 3. Create or get Bays
    bays_data = [
        (site_a.id, "Bay A1 - Standard", "Standard Inspection", BayStatus.AVAILABLE),
        (site_a.id, "Bay A2 - Express", "Fast Verification", BayStatus.AVAILABLE),
        (site_a.id, "Bay A3 - Heavy Duty", "Heavy Cargo Inspection", BayStatus.AVAILABLE),
        (site_b.id, "Bay B1 - Cargo Main", "Standard Inspection", BayStatus.AVAILABLE),
        (site_b.id, "Bay B2 - Hazmat Check", "Hazardous Materials", BayStatus.AVAILABLE),
        (site_c.id, "Bay C1 - Primary", "Standard Inspection", BayStatus.AVAILABLE),
        (site_c.id, "Bay C2 - Secondary", "Safety Audit", BayStatus.AVAILABLE),
    ]
    for s_id, b_name, b_type, b_status in bays_data:
        if not db.query(Bay).filter_by(site_id=s_id, bay_name=b_name).first():
            bay = Bay(site_id=s_id, bay_name=b_name, bay_type=b_type, status=b_status)
            db.add(bay)
    db.flush()

    # 4. Create Users (Demo accounts for all 5 RBAC roles)
    hashed_pwd = get_password_hash("password123")
    users_data = [
        {"email": "operator@sitea.com", "password_hash": hashed_pwd, "full_name": "Alex Operator", "role": UserRole.OPERATOR, "site_id": site_a.id},
        {"email": "sitemanager@sitea.com", "password_hash": hashed_pwd, "full_name": "Sarah Site Manager", "role": UserRole.SITE_MANAGER, "site_id": site_a.id},
        {"email": "regional@system.com", "password_hash": hashed_pwd, "full_name": "Robert Regional Director", "role": UserRole.REGIONAL_MANAGER, "site_id": None},
        {"email": "auditor@system.com", "password_hash": hashed_pwd, "full_name": "Amanda Auditor", "role": UserRole.AUDITOR, "site_id": None},
        {"email": "admin@system.com", "password_hash": hashed_pwd, "full_name": "Arthur System Admin", "role": UserRole.ADMIN, "site_id": None},
    ]
    for u_data in users_data:
        if not db.query(User).filter_by(email=u_data["email"]).first():
            user = User(**u_data)
            db.add(user)
    db.flush()

    # 5. Create Demo Vehicles & Completed Journeys for rich dashboard KPIs
    vehicles_data = [
        {"vehicle_number": "DL01AB1234", "make": "Volvo", "model": "FH16", "category": "Commercial Truck", "owner_name": "Express Cargo Ltd", "compliance_status": "ELIGIBLE"},
        {"vehicle_number": "MH02CD5678", "make": "Freightliner", "model": "Cascadia", "category": "Container Hauler", "owner_name": "National Freight Inc", "compliance_status": "ELIGIBLE"},
        {"vehicle_number": "KA03EF9012", "make": "Tata", "model": "Prima 4928", "category": "Heavy Transport", "owner_name": "Deccan Logistics", "compliance_status": "NON_COMPLIANT"},
    ]
    vehicles = {}
    for v_data in vehicles_data:
        veh = db.query(Vehicle).filter_by(vehicle_number=v_data["vehicle_number"]).first()
        if not veh:
            veh = Vehicle(**v_data)
            db.add(veh)
            db.flush()
        vehicles[v_data["vehicle_number"]] = veh

    v1 = vehicles["DL01AB1234"]
    v2 = vehicles["MH02CD5678"]

    now = datetime.utcnow()

    # Past Completed Journey 1
    j1_exists = db.query(Journey).filter_by(vehicle_id=v1.id, site_id=site_a.id).first()
    if not j1_exists:
        j1 = Journey(
            vehicle_id=v1.id,
            site_id=site_a.id,
            entry_camera_id=cam_a_in.id,
            exit_camera_id=cam_a_out.id,
            current_state=JourneyState.EXITED,
            anpr_confidence=0.96,
            entry_time=now - timedelta(hours=2, minutes=30),
            bay_assigned_time=now - timedelta(hours=2, minutes=20),
            service_start_time=now - timedelta(hours=2, minutes=15),
            service_end_time=now - timedelta(hours=1, minutes=45),
            exit_time=now - timedelta(hours=1, minutes=40)
        )
        db.add(j1)

    # Past Completed Journey 2
    j2_exists = db.query(Journey).filter_by(vehicle_id=v2.id, site_id=site_b.id).first()
    if not j2_exists:
        j2 = Journey(
            vehicle_id=v2.id,
            site_id=site_b.id,
            entry_camera_id=cam_b_in.id,
            exit_camera_id=cam_b_out.id,
            current_state=JourneyState.EXITED,
            anpr_confidence=0.94,
            entry_time=now - timedelta(hours=1, minutes=45),
            bay_assigned_time=now - timedelta(hours=1, minutes=35),
            service_start_time=now - timedelta(hours=1, minutes=30),
            service_end_time=now - timedelta(minutes=50),
            exit_time=now - timedelta(minutes=45)
        )
        db.add(j2)

    db.commit()


def seed(drop_existing: bool = False):
    if drop_existing:
        logger.info("Dropping and re-creating database tables for fresh seed...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    else:
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        populate_demo_data(db)
        logger.info("Successfully seeded database with demo sites, cameras, bays, RBAC users, and initial journeys!")
    except Exception as e:
        logger.error(f"Error seeding database: {e}", exc_info=True)
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed(drop_existing=True)
