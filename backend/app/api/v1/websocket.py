"""WebSocket endpoint for real-time updates."""

import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import study
from app.db.session import AsyncSessionLocal
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
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@router.websocket("/studies")
async def websocket_studies_endpoint(websocket: WebSocket):
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
        async with AsyncSessionLocal() as db:
            try:
                studies_data = await study.get_multi(db, skip=0, limit=100)
                # Convert SQLAlchemy models to Pydantic schemas
                studies_json = [Study.model_validate(study_item).model_dump() for study_item in studies_data]
                await manager.send_personal_message(
                    json.dumps({
                        "type": "studies_update",
                        "data": studies_json
                    }),
                    websocket
                )
                logger.info(f"Sent initial data with {len(studies_json)} studies")
            except Exception as e:
                logger.error(f"Error sending initial data: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": f"Error loading initial data: {str(e)}"
                    }),
                    websocket
                )
        
        # Listen for client messages
        while True:
            try:
                # Check if WebSocket is still connected
                if websocket.client_state.name != "CONNECTED":
                    logger.info("WebSocket no longer connected, breaking message loop")
                    break
                    
                # Add timeout to prevent hanging
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    logger.info(f"Received WebSocket message: {data}")
                except asyncio.TimeoutError:
                    # Send keep-alive ping if no message received
                    logger.debug("WebSocket timeout, sending keep-alive ping")
                    await manager.send_personal_message(
                        json.dumps({"type": "ping"}),
                        websocket
                    )
                    continue
                message = json.loads(data)
                
                if message.get("action") == "refresh":
                    # Client requests data refresh
                    async with AsyncSessionLocal() as db:
                        try:
                            studies_data = await study.get_multi(db, skip=0, limit=100)
                            # Convert SQLAlchemy models to Pydantic schemas
                            studies_json = [Study.model_validate(study_item).model_dump() for study_item in studies_data]
                            await manager.send_personal_message(
                                json.dumps({
                                    "type": "studies_update",
                                    "data": studies_json
                                }),
                                websocket
                            )
                            logger.info(f"Sent refresh data with {len(studies_json)} studies")
                        except Exception as e:
                            logger.error(f"Error during refresh: {e}")
                            await manager.send_personal_message(
                                json.dumps({
                                    "type": "error",
                                    "message": f"Error refreshing data: {str(e)}"
                                }),
                                websocket
                            )
                elif message.get("action") == "ping":
                    # Keep connection alive
                    await manager.send_personal_message(
                        json.dumps({"type": "pong"}),
                        websocket
                    )
                    logger.info("Sent pong response")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                try:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }),
                        websocket
                    )
                except Exception:
                    logger.error("Failed to send error message, breaking loop")
                    break
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during message processing")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                try:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": "Error processing message"
                        }),
                        websocket
                    )
                except Exception:
                    logger.error("Failed to send error message, breaking loop")
                    break
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_study_created(study_data):
    """Broadcast that a new study was created."""
    logger.info(f"🚀 Broadcasting study_created: {study_data.study_label}")
    # Convert SQLAlchemy model to Pydantic schema
    pydantic_study = Study.model_validate(study_data)
    message = json.dumps({
        "type": "study_created",
        "data": pydantic_study.model_dump()
    })
    await manager.broadcast(message)
    logger.info(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_study_updated(study_data):
    """Broadcast that a study was updated."""
    logger.info(f"📝 Broadcasting study_updated: {study_data.study_label}")
    # Convert SQLAlchemy model to Pydantic schema
    pydantic_study = Study.model_validate(study_data)
    message = json.dumps({
        "type": "study_updated",
        "data": pydantic_study.model_dump()
    })
    await manager.broadcast(message)
    logger.info(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_study_deleted(study_id: int):
    """Broadcast that a study was deleted."""
    logger.info(f"🗑️ Broadcasting study_deleted: ID {study_id}")
    message = json.dumps({
        "type": "study_deleted",
        "data": {"id": study_id}
    })
    await manager.broadcast(message)
    logger.info(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_studies_refresh():
    """Broadcast a signal to refresh studies data."""
    message = json.dumps({
        "type": "refresh_needed"
    })
    await manager.broadcast(message)