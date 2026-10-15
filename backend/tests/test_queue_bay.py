import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
import app.models
from app.models.sites import Site, SiteStatus
from app.models.vehicles import Vehicle
from app.models.journeys import Journey, JourneyState
from app.models.bays import Bay, BayStatus
from app.models.queues import QueueItem, QueueStatus
from app.services.queue_service import QueueService
from app.services.bay_service import BayService

@pytest.fixture
def queue_bay_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    site = Site(name="North Hub", code="NH-01", location="Sector 1", status=SiteStatus.ONLINE, max_queue_capacity=10)
    session.add(site)
    session.commit()

    # Create 1 bay
    bay = Bay(site_id=site.id, bay_name="Bay 1", bay_type="Inspection", status=BayStatus.AVAILABLE)
    session.add(bay)
    session.commit()

    # Create 2 vehicles and 2 journeys
    v1 = Vehicle(vehicle_number="KA01-1111", make="Tata", model="Prima", compliance_status="ELIGIBLE")
    v2 = Vehicle(vehicle_number="MH02-2222", make="Ashok", model="Leyland", compliance_status="ELIGIBLE")
    session.add_all([v1, v2])
    session.commit()

    j1 = Journey(vehicle_id=v1.id, site_id=site.id, current_state=JourneyState.ELIGIBLE, entry_time=datetime.utcnow())
    j2 = Journey(vehicle_id=v2.id, site_id=site.id, current_state=JourneyState.ELIGIBLE, entry_time=datetime.utcnow())
    session.add_all([j1, j2])
    session.commit()

    yield session, site, bay, j1, j2
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_queue_ordering_and_dequeue(queue_bay_db):
    session, site, bay, j1, j2 = queue_bay_db

    # 1. Enqueue journey 1
    q1 = QueueService.enqueue(session, j1, priority=1)
    assert q1.position == 1
    assert q1.status == QueueStatus.WAITING

    # 2. Enqueue journey 2
    q2 = QueueService.enqueue(session, j2, priority=1)
    assert q2.position == 2
    assert q2.status == QueueStatus.WAITING

    # 3. Dequeue journey 1
    QueueService.dequeue(session, j1.id)
    session.refresh(q1)
    assert q1.status == QueueStatus.ASSIGNED

    # 4. Journey 2 position should now adjust to 1
    session.refresh(q2)
    assert q2.position == 1

def test_bay_auto_assignment_and_saturation(queue_bay_db):
    session, site, bay, j1, j2 = queue_bay_db

    # 1. Auto assign bay to journey 1 (bay is available)
    assigned_bay = BayService.auto_assign_bay(session, j1)
    assert assigned_bay is not None
    assert assigned_bay.id == bay.id
    assert assigned_bay.status == BayStatus.RESERVED
    assert assigned_bay.current_journey_id == j1.id

    # 2. Attempt auto assign for journey 2 (no more bays available)
    no_bay = BayService.auto_assign_bay(session, j2)
    assert no_bay is None
