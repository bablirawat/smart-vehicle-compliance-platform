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

# Auto create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc) if not settings.SECRET_KEY.startswith("super") else "An internal server error occurred."
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
