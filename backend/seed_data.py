import logging
from datetime import datetime, timedelta
from app.database import SessionLocal, Base, engine
import app.models # Register models
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

def seed():
    logger.info("Dropping and re-creating database tables for fresh seed...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Create Sites
        site_a = Site(name="North Terminal Logistics Hub", code="SITE-A", location="Delhi NCR Hub", status=SiteStatus.ONLINE, max_queue_capacity=10)
        site_b = Site(name="East Coast Cargo Station", code="SITE-B", location="Mumbai Port Terminal", status=SiteStatus.ONLINE, max_queue_capacity=8)
        site_c = Site(name="South Freight Transit Hub", code="SITE-C", location="Bengaluru Outer Ring", status=SiteStatus.ONLINE, max_queue_capacity=12)

        db.add_all([site_a, site_b, site_c])
        db.commit()
        db.refresh(site_a)
        db.refresh(site_b)
        db.refresh(site_c)

        # 2. Create Cameras
        cam_a_in = Camera(site_id=site_a.id, camera_code="CAM-A-ENTRY-01", type=CameraType.ENTRY, status=CameraStatus.ONLINE)
        cam_a_out = Camera(site_id=site_a.id, camera_code="CAM-A-EXIT-01", type=CameraType.EXIT, status=CameraStatus.ONLINE)
        
        cam_b_in = Camera(site_id=site_b.id, camera_code="CAM-B-ENTRY-01", type=CameraType.ENTRY, status=CameraStatus.ONLINE)
        cam_b_out = Camera(site_id=site_b.id, camera_code="CAM-B-EXIT-01", type=CameraType.EXIT, status=CameraStatus.ONLINE)

        cam_c_in = Camera(site_id=site_c.id, camera_code="CAM-C-ENTRY-01", type=CameraType.ENTRY, status=CameraStatus.ONLINE)
        cam_c_out = Camera(site_id=site_c.id, camera_code="CAM-C-EXIT-01", type=CameraType.EXIT, status=CameraStatus.ONLINE)

        db.add_all([cam_a_in, cam_a_out, cam_b_in, cam_b_out, cam_c_in, cam_c_out])
        db.commit()

        # 3. Create Bays
        bays_a = [
            Bay(site_id=site_a.id, bay_name="Bay A1 - Standard", bay_type="Standard Inspection", status=BayStatus.AVAILABLE),
            Bay(site_id=site_a.id, bay_name="Bay A2 - Express", bay_type="Fast Verification", status=BayStatus.AVAILABLE),
            Bay(site_id=site_a.id, bay_name="Bay A3 - Heavy Duty", bay_type="Heavy Cargo Inspection", status=BayStatus.AVAILABLE),
        ]
        bays_b = [
            Bay(site_id=site_b.id, bay_name="Bay B1 - Cargo Main", bay_type="Standard Inspection", status=BayStatus.AVAILABLE),
            Bay(site_id=site_b.id, bay_name="Bay B2 - Hazmat Check", bay_type="Hazardous Materials", status=BayStatus.AVAILABLE),
        ]
        bays_c = [
            Bay(site_id=site_c.id, bay_name="Bay C1 - Primary", bay_type="Standard Inspection", status=BayStatus.AVAILABLE),
            Bay(site_id=site_c.id, bay_name="Bay C2 - Secondary", bay_type="Safety Audit", status=BayStatus.AVAILABLE),
        ]
        db.add_all(bays_a + bays_b + bays_c)
        db.commit()

        # 4. Create Users (Demo accounts for all 5 RBAC roles)
        hashed_pwd = get_password_hash("password123")
        users = [
            User(email="operator@sitea.com", password_hash=hashed_pwd, full_name="Alex Operator", role=UserRole.OPERATOR, site_id=site_a.id),
            User(email="sitemanager@sitea.com", password_hash=hashed_pwd, full_name="Sarah Site Manager", role=UserRole.SITE_MANAGER, site_id=site_a.id),
            User(email="regional@system.com", password_hash=hashed_pwd, full_name="Robert Regional Director", role=UserRole.REGIONAL_MANAGER, site_id=None),
            User(email="auditor@system.com", password_hash=hashed_pwd, full_name="Amanda Auditor", role=UserRole.AUDITOR, site_id=None),
            User(email="admin@system.com", password_hash=hashed_pwd, full_name="Arthur System Admin", role=UserRole.ADMIN, site_id=None),
        ]
        db.add_all(users)
        db.commit()

        # 5. Create Demo Vehicles & Completed Journeys for rich dashboard KPIs
        v1 = Vehicle(vehicle_number="DL01AB1234", make="Volvo", model="FH16", category="Commercial Truck", owner_name="Express Cargo Ltd", compliance_status="ELIGIBLE")
        v2 = Vehicle(vehicle_number="MH02CD5678", make="Freightliner", model="Cascadia", category="Container Hauler", owner_name="National Freight Inc", compliance_status="ELIGIBLE")
        v3 = Vehicle(vehicle_number="KA03EF9012", make="Tata", model="Prima 4928", category="Heavy Transport", owner_name="Deccan Logistics", compliance_status="NON_COMPLIANT")
        db.add_all([v1, v2, v3])
        db.commit()

        now = datetime.utcnow()

        # Past Completed Journey 1
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

        logger.info("Successfully seeded database with demo sites, cameras, bays, RBAC users, and initial journeys!")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
