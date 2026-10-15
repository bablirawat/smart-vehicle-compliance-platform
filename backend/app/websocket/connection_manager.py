import logging
import json
from typing import Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger("websocket_manager")

class ConnectionManager:
    def __init__(self):
        # site_id -> set of WebSockets
        self.site_connections: Dict[int, Set[WebSocket]] = {}
        # central WebSocket connections
        self.central_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, site_id: int = None):
        await websocket.accept()
        if site_id:
            if site_id not in self.site_connections:
                self.site_connections[site_id] = set()
            self.site_connections[site_id].add(websocket)
        else:
            self.central_connections.add(websocket)
        logger.info(f"WebSocket connected. Site: {site_id}")

    def disconnect(self, websocket: WebSocket, site_id: int = None):
        if site_id and site_id in self.site_connections:
            self.site_connections[site_id].discard(websocket)
            if not self.site_connections[site_id]:
                del self.site_connections[site_id]
        else:
            self.central_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Site: {site_id}")

    async def broadcast_to_site(self, site_id: int, message: dict):
        payload = json.dumps(message)
        # Broadcast to site listeners
        if site_id in self.site_connections:
            for ws in list(self.site_connections[site_id]):
                try:
                    await ws.send_text(payload)
                except Exception as e:
                    logger.warning(f"Error sending to site ws: {e}")
                    self.disconnect(ws, site_id)
        # Also broadcast to central command listeners
        for ws in list(self.central_connections):
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"Error sending to central ws: {e}")
                self.disconnect(ws)

    async def broadcast_central(self, message: dict):
        payload = json.dumps(message)
        for ws in list(self.central_connections):
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"Error sending to central ws: {e}")
                self.disconnect(ws)

manager = ConnectionManager()
