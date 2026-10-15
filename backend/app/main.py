import os
import sys
from pathlib import Path
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import engine, Base
import app.models # Register all ORM models

from app.api.auth import router as auth_router
from app.api.sites import router as sites_router
from app.api.events import router as events_router
from app.api.journeys import router as journeys_router
from app.api.queues import router as queues_router
from app.api.bays import router as bays_router
from app.api.service import router as service_router
from app.api.alerts import router as alerts_router
from app.api.dashboard import router as dashboard_router
from app.api.audit import router as audit_router
from app.api.simulator import router as simulator_router
from app.websocket.connection_manager import manager
from app.state_machine.journey_state_machine import InvalidStateTransitionException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Auto create database tables on module load
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware: explicitly configure local development and production origins
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Allow specifying frontend origins via FRONTEND_ORIGIN or CORS_ORIGINS
for env_name in ("FRONTEND_ORIGIN", "CORS_ORIGINS"):
    env_val = os.getenv(env_name)
    if env_val:
        for origin in env_val.split(","):
            clean_origin = origin.strip().rstrip("/")
            if clean_origin and clean_origin not in cors_origins:
                cors_origins.append(clean_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_init():
    """Validate configuration and ensure database is safely initialized."""
    # 1. Enforce production security check: prevent silent startup with default secret
    is_production = settings.ENVIRONMENT.lower() in ("production", "prod") or bool(os.getenv("RENDER"))
    if is_production:
        if not settings.SECRET_KEY or settings.SECRET_KEY == "super-secret-production-key-change-in-prod-123456789" or len(settings.SECRET_KEY) < 32:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: Running in production with an unset, default, or weak SECRET_KEY is prohibited. "
                "Set a secure, random SECRET_KEY environment variable (minimum 32 characters) in your production host settings."
            )
        logger.info("Production security check: Strong custom SECRET_KEY verified.")
    else:
        if settings.SECRET_KEY == "super-secret-production-key-change-in-prod-123456789":
            logger.warning("Running in DEVELOPMENT mode with default SECRET_KEY. Configure a unique SECRET_KEY before deploying to production.")

    # 2. Database table verification & safe empty-check auto-seeding
    Base.metadata.create_all(bind=engine)
    try:
        backend_dir = str(Path(__file__).resolve().parent.parent)
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from seed_data import populate_demo_data
        from app.database import SessionLocal
        from app.models.sites import Site
        from app.models.users import User
        from app.models.vehicles import Vehicle

        db = SessionLocal()
        try:
            site_count = db.query(Site).count()
            user_count = db.query(User).count()
            vehicle_count = db.query(Vehicle).count()

            if site_count == 0 and user_count == 0 and vehicle_count == 0:
                logger.info("Fresh database detected (0 sites, 0 users, 0 vehicles). Auto-seeding initial demo data...")
                populate_demo_data(db)
                logger.info("Demo data seeding completed successfully on startup.")
            else:
                logger.info(
                    f"Existing database verified ({site_count} sites, {user_count} users, {vehicle_count} vehicles found). "
                    "Skipping auto-seed to preserve existing records."
                )
        except Exception as seed_err:
            db.rollback()
            logger.critical(f"FATAL: Database auto-seeding failed: {seed_err}", exc_info=True)
            raise seed_err
        finally:
            db.close()
    except Exception as e:
        logger.critical(f"FATAL: Database startup initialization failed: {e}", exc_info=True)
        raise e

# Custom centralized error handler for state machine invalid transitions
@app.exception_handler(InvalidStateTransitionException)
async def state_transition_exception_handler(request: Request, exc: InvalidStateTransitionException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "INVALID_STATE_TRANSITION",
                "message": exc.reason,
                "current_state": exc.current_state,
                "target_state": exc.target_state
            }
        }
    )

# Generic exception handler for structured API errors
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system exception: {exc}", exc_info=True)
    is_production = settings.ENVIRONMENT.lower() in ("production", "prod") or bool(os.getenv("RENDER"))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred." if is_production else str(exc)
            }
        }
    )

# Include API V1 routers
v1_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=v1_prefix)
app.include_router(sites_router, prefix=v1_prefix)
app.include_router(events_router, prefix=v1_prefix)
app.include_router(journeys_router, prefix=v1_prefix)
app.include_router(queues_router, prefix=v1_prefix)
app.include_router(bays_router, prefix=v1_prefix)
app.include_router(service_router, prefix=v1_prefix)
app.include_router(alerts_router, prefix=v1_prefix)
app.include_router(dashboard_router, prefix=v1_prefix)
app.include_router(audit_router, prefix=v1_prefix)
app.include_router(simulator_router, prefix=v1_prefix)

@app.get("/")
def root():
    return {
        "title": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "websocket": "/ws/sites/{site_id}"
    }

# WebSockets Endpoints
@app.websocket("/ws/sites/{site_id}")
async def site_websocket_endpoint(websocket: WebSocket, site_id: int):
    await manager.connect(websocket, site_id=site_id)
    try:
        while True:
            # Keepalive ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, site_id=site_id)

@app.websocket("/ws/central")
async def central_websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket, site_id=None)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, site_id=None)
