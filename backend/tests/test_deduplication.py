import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
import app.models  # Register all models on Base.metadata
from app.models.sites import Site, SiteStatus
from app.models.cameras import Camera, CameraType, CameraStatus
from app.services.journey_service import journey_service

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed minimal site and camera
    site = Site(name="Test Terminal", code="TEST-01", location="Test City", status=SiteStatus.ONLINE)
    session.add(site)
    session.commit()

    camera = Camera(site_id=site.id, camera_code="CAM-ENT-01", type=CameraType.ENTRY, status=CameraStatus.ONLINE)
    session.add(camera)
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_deduplication_suppression(db_session):
    site = db_session.query(Site).first()
    camera = db_session.query(Camera).first()

    # 1. First vehicle entry
    j1, is_dup1 = journey_service.process_vehicle_entry(
        db=db_session,
        site_id=site.id,
        camera_id=camera.id,
        vehicle_number="KA01-TEST-1234",
        confidence=0.98
    )
    assert is_dup1 is False
    assert j1.id is not None
    assert j1.vehicle.vehicle_number == "KA01-TEST-1234"

    # 2. Immediate duplicate ANPR trigger within 60s window
    j2, is_dup2 = journey_service.process_vehicle_entry(
        db=db_session,
        site_id=site.id,
        camera_id=camera.id,
        vehicle_number="KA01-TEST-1234",
        confidence=0.95
    )
    assert is_dup2 is True
    assert j2.id == j1.id

    # 3. Different vehicle entry should not be suppressed
    j3, is_dup3 = journey_service.process_vehicle_entry(
        db=db_session,
        site_id=site.id,
        camera_id=camera.id,
        vehicle_number="MH02-OTHER-5678",
        confidence=0.99
    )
    assert is_dup3 is False
    assert j3.id != j1.id
