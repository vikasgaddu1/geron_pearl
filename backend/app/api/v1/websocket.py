"""WebSocket endpoint for real-time updates."""

import json
import logging
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import study
from app.db.session import get_db
from app.schemas.study import Study

logger = logging.getLogger(__name__)

router = APIRouter()

# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
            
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSocket clients."""
        if not self.active_connections:
            return
            
        disconnected = set()
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
                
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

# Global connection manager instance
manager = ConnectionManager()


async def get_websocket_db():
    """Dependency to get database session for WebSocket endpoints."""
    from app.db.session import async_session_maker
    async with async_session_maker() as session:
        yield session


@router.websocket("/studies")
async def websocket_studies_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_websocket_db)
):
    """
    WebSocket endpoint for real-time study updates.
    
    Clients can send messages to request data refresh:
    - {"action": "refresh"} - Request latest studies data
    - {"action": "ping"} - Keep connection alive
    
    Server sends updates:
    - {"type": "studies_update", "data": [...]} - Studies data update
    - {"type": "study_created", "data": {...}} - New study created
    - {"type": "study_updated", "data": {...}} - Study updated
    - {"type": "study_deleted", "data": {"id": ...}} - Study deleted
    - {"type": "error", "message": "..."} - Error message
    - {"type": "pong"} - Response to ping
    """
    await manager.connect(websocket)
    
    try:
        # Send initial data
        studies_data = await study.get_multi(db, skip=0, limit=100)
        studies_json = [study_item.model_dump() for study_item in studies_data]
        await manager.send_personal_message(
            json.dumps({
                "type": "studies_update",
                "data": studies_json
            }),
            websocket
        )
        
        # Listen for client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("action") == "refresh":
                    # Client requests data refresh
                    studies_data = await study.get_multi(db, skip=0, limit=100)
                    studies_json = [study_item.model_dump() for study_item in studies_data]
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "studies_update",
                            "data": studies_json
                        }),
                        websocket
                    )
                elif message.get("action") == "ping":
                    # Keep connection alive
                    await manager.send_personal_message(
                        json.dumps({"type": "pong"}),
                        websocket
                    )
                    
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }),
                    websocket
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Error processing message"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_study_created(study_data: Study):
    """Broadcast that a new study was created."""
    message = json.dumps({
        "type": "study_created",
        "data": study_data.model_dump()
    })
    await manager.broadcast(message)


async def broadcast_study_updated(study_data: Study):
    """Broadcast that a study was updated."""
    message = json.dumps({
        "type": "study_updated",
        "data": study_data.model_dump()
    })
    await manager.broadcast(message)


async def broadcast_study_deleted(study_id: int):
    """Broadcast that a study was deleted."""
    message = json.dumps({
        "type": "study_deleted",
        "data": {"id": study_id}
    })
    await manager.broadcast(message)


async def broadcast_studies_refresh():
    """Broadcast a signal to refresh studies data."""
    message = json.dumps({
        "type": "refresh_needed"
    })
    await manager.broadcast(message)