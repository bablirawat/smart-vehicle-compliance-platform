# Smart Vehicle Compliance & Journey Management Platform

Production-style end-to-end full-stack platform for vehicle identity verification, compliance check, queue management, bay allocation, real-time event broadcasting, and multi-site operations.

---

## 1. Project Overview

The **Smart Vehicle Compliance & Journey Management Platform** orchestrates the end-to-end lifecycle of commercial vehicles passing through logistics checkpoints, inspection stations, and port terminals. It replaces static CRUD operations with an **explicit backend state machine**, **real-time WebSocket broadcasting**, **simulated external identity & compliance verification services**, **automated queue & bay management**, **multi-site RBAC**, **timestamp-based KPI analytics**, and an **interactive simulator**.

---

## 2. Core Business Flow & State Machine

Every vehicle journey progresses through strict, validated backend state transitions:

```
ENTERED → IDENTIFIED → VERIFIED → ELIGIBLE / NOT_ELIGIBLE → QUEUED → BAY_ASSIGNED → IN_SERVICE → SERVICE_COMPLETED → EXITED
                                         ↓
                                       HOLD (Operator Review / Manager Override)
```

- **ENTERED**: ANPR camera detects vehicle license plate & records confidence.
- **IDENTIFIED**: Vehicle details created or resolved in database.
- **VERIFIED**: External identity & compliance verification APIs queried.
- **ELIGIBLE**: Eligibility Engine evaluates rules (VALID -> ELIGIBLE, DUE_SOON -> ELIGIBLE with warning, EXPIRED/INVALID -> HOLD, UNAVAILABLE -> HOLD).
- **QUEUED**: Eligible vehicle placed into live site queue.
- **BAY_ASSIGNED**: Concurrency-safe bay lock matches vehicle to available inspection bay.
- **IN_SERVICE**: Operator starts inspection service session.
- **SERVICE_COMPLETED**: Inspection finished, duration recorded, bay released.
- **EXITED**: Exit ANPR camera records vehicle exit, completing journey.

---

## 3. Technology Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic V2, SQLAlchemy 2.0 ORM, PyJWT, Passlib (PBKDF2 SHA256), WebSockets, Pytest.
- **Database**: SQLite (`sqlite:///./smart_vehicle.db`) for instant zero-dependency execution out-of-the-box, fully configurable via `.env` to MySQL (`mysql+pymysql://...`).
- **Frontend**: React 18, Vite, React Router v6, Axios, Lucide React Icons, Recharts, Native WebSocket Client, Vanilla Enterprise CSS.
- **Tools**: Postman / Bruno API Collection, Docker Compose.

---

## 4. Quick Start & Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+

### Step 1: Start Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Seed database with demo sites, cameras, bays, RBAC users & initial data
python seed_data.py

# Run FastAPI server
uvicorn app.main:app --reload --port 8000
```
- Swagger API Docs: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

### Step 2: Start Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- Web Application: `http://localhost:3000`

---

## 5. Demo Role Credentials (RBAC)

Password for all demo accounts: `password123`

| Role | Email | Scope | Capabilities |
| :--- | :--- | :--- | :--- |
| **Operator** | `operator@sitea.com` | Site A | Process vehicles, assign bays, start/complete service, acknowledge alerts, hold/release. |
| **Site Manager** | `sitemanager@sitea.com` | Site A | Manage bays, override decisions with reason, view site reports. |
| **Regional Manager**| `regional@system.com` | All Sites | View central command dashboard, compare sites, monitor network queue. |
| **Auditor** | `auditor@system.com` | All Sites | View journey history & immutable audit logs, export CSV report (read-only). |
| **Admin** | `admin@system.com` | All Sites | Full system access, manage users, sites & system configuration. |

---

## 6. Failure & Edge Case Scenarios

The system natively handles and demonstrates all 10 required edge-case scenarios:

1. **Normal Eligible Journey**: Vehicle enters -> passes verification -> queued -> bay assigned -> service completed -> exit.
2. **Non-Eligible Vehicle**: Fails compliance -> auto-moved to `HOLD` state -> raises High severity alert.
3. **External Verification Unavailable**: Simulates API gateway timeout -> marks `SOURCE_UNAVAILABLE` -> moves to `HOLD` for operator review.
4. **Camera Offline**: Toggles ANPR camera status to `OFFLINE` -> raises High severity camera alert -> updates site status to WARNING.
5. **Duplicate Vehicle Entry**: Second entry event within 60s window suppressed by deduplication engine (`is_duplicate=true`).
6. **Queue Overload**: Flooding site queue triggers `QUEUE_OVERLOAD` alert when capacity exceeded.
7. **Bay Occupancy Lock**: Concurrency-safe DB lock prevents double assignment of the same bay to multiple vehicles.
8. **Operator Override**: Requires authorized manager role & mandatory reason string (stored in audit logs).
9. **WebSocket Auto-Reconnect**: Re-establishes connection automatically if disconnected.
10. **Multi-Site Operations**: Simultaneous real-time monitoring across Site A, Site B, and Site C.

---

## 7. Architecture & System Q&A

### What did you build?
A complete, production-grade Smart Vehicle Compliance & Journey Management Platform supporting real-time vehicle lifecycle tracking, external verification simulation, automated queue/bay assignment, multi-site RBAC, and timestamp-based KPI analytics.

### Why this architecture?
A clean service-oriented architecture (FastAPI + SQLAlchemy + React + WebSockets) separates API endpoints, state machine validation, business logic, persistence, and presentation. WebSockets eliminate polling overhead while preserving real-time dashboard updates.

### How does event flow work?
Vehicle entry API -> Deduplication Check -> DB Vehicle Record -> Journey Created -> Verification Services -> Eligibility Engine -> State Machine Transition -> Queue & Bay Assignment -> WebSocket Broadcast -> React UI Update.

### How are duplicate events handled?
The backend checks for matching `(site_id, vehicle_number)` within a configurable deduplication window (`DEDUPLICATION_WINDOW_SECONDS=60`). If a duplicate arrives, the system logs an audit record and suppresses duplicate journey creation.

### How are invalid transitions prevented?
The `JourneyStateMachine` strictly enforces allowed transition paths. Any invalid transition (e.g. `ENTERED` -> `IN_SERVICE`) throws an `InvalidStateTransitionException` returning HTTP 422 with a structured error payload.

### How are permissions enforced?
Permissions are enforced strictly on the backend via PyJWT token verification and FastAPI `require_roles` dependency injection.

### How would you scale from 5 sites to 1,000 sites?
1. **Horizontal API Scaling**: Stateless FastAPI container instances behind an NGINX / ALB load balancer.
2. **Message Broker & Event Bus**: Replace in-memory WebSocket manager with **Redis Pub/Sub** or **Apache Kafka**.
3. **Database Scaling**: Read replicas for analytical queries, database sharding/partitioning by `site_id`, and Redis caching for site metadata and bay states.
4. **WebSocket Gateway**: Dedicated WebSocket gateway nodes for managing persistent client socket connections.

---

## 8. Automated Backend Tests

Run the test suite via pytest:
```bash
cd backend
python -m pytest tests/
```

Includes test cases for:
- State Machine valid sequence & invalid transition blocking
- Eligibility Engine rule evaluation
- Deduplication window logic
- RBAC permissions
