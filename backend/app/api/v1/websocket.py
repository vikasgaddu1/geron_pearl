"""WebSocket endpoint for real-time updates."""

import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import study, database_release, reporting_effort
from app.db.session import AsyncSessionLocal
from app.schemas.study import Study
from app.schemas.database_release import DatabaseRelease
from app.schemas.reporting_effort import ReportingEffort

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
        
    def cleanup_stale_connections(self):
        """Remove connections that are no longer in CONNECTED state."""
        stale_connections = set()
        
        for connection in self.active_connections.copy():
            try:
                if hasattr(connection, 'client_state') and connection.client_state.name != "CONNECTED":
                    stale_connections.add(connection)
            except Exception:
                # If we can't check the state, assume it's stale
                stale_connections.add(connection)
                
        for connection in stale_connections:
            self.disconnect(connection)
            
        if stale_connections:
            logger.info(f"Cleaned up {len(stale_connections)} stale connections")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
            
    async def broadcast(self, message: str):
        """Broadcast a message to all connected WebSocket clients."""
        # Clean up stale connections before broadcasting
        self.cleanup_stale_connections()
        
        if not self.active_connections:
            logger.debug("No active connections for broadcast")
            return
            
        disconnected = set()
        successful_sends = 0
        
        for connection in self.active_connections.copy():
            try:
                # Check connection state before attempting to send
                if hasattr(connection, 'client_state') and connection.client_state.name != "CONNECTED":
                    logger.debug(f"Connection not in CONNECTED state: {connection.client_state.name}")
                    disconnected.add(connection)
                    continue
                    
                await connection.send_text(message)
                successful_sends += 1
                
            except Exception as e:
                logger.debug(f"Connection broadcast failed, marking for removal: {e}")
                disconnected.add(connection)
                
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
            
        logger.debug(f"Broadcast completed: {successful_sends} successful, {len(disconnected)} removed")

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
    logger.debug(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


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
    logger.debug(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_study_deleted(study_id: int):
    """Broadcast that a study was deleted."""
    logger.info(f"🗑️ Broadcasting study_deleted: ID {study_id}")
    message = json.dumps({
        "type": "study_deleted",
        "data": {"id": study_id}
    })
    await manager.broadcast(message)
    logger.debug(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_studies_refresh():
    """Broadcast a signal to refresh studies data."""
    message = json.dumps({
        "type": "refresh_needed"
    })
    await manager.broadcast(message)


async def broadcast_database_release_created(database_release_data):
    """Broadcast that a new database release was created."""
    logger.info(f"🚀 Broadcasting database_release_created: {database_release_data.database_release_label}")
    # Convert SQLAlchemy model to Pydantic schema
    pydantic_database_release = DatabaseRelease.model_validate(database_release_data)
    message = json.dumps({
        "type": "database_release_created",
        "data": pydantic_database_release.model_dump()
    })
    await manager.broadcast(message)
    logger.debug(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_database_release_updated(database_release_data):
    """Broadcast that a database release was updated."""
    logger.info(f"📝 Broadcasting database_release_updated: {database_release_data.database_release_label}")
    # Convert SQLAlchemy model to Pydantic schema
    pydantic_database_release = DatabaseRelease.model_validate(database_release_data)
    message = json.dumps({
        "type": "database_release_updated",
        "data": pydantic_database_release.model_dump()
    })
    await manager.broadcast(message)
    logger.debug(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_database_release_deleted(database_release_id: int):
    """Broadcast that a database release was deleted."""
    logger.info(f"🗑️ Broadcasting database_release_deleted: ID {database_release_id}")
    message = json.dumps({
        "type": "database_release_deleted",
        "data": {"id": database_release_id}
    })
    await manager.broadcast(message)
    logger.debug(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_reporting_effort_created(reporting_effort_data):
    """Broadcast that a new reporting effort was created."""
    logger.info(f"🚀 Broadcasting reporting_effort_created: {reporting_effort_data.database_release_label}")
    # Convert SQLAlchemy model to Pydantic schema
    pydantic_reporting_effort = ReportingEffort.model_validate(reporting_effort_data)
    message = json.dumps({
        "type": "reporting_effort_created",
        "data": pydantic_reporting_effort.model_dump()
    })
    await manager.broadcast(message)
    logger.debug(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_reporting_effort_updated(reporting_effort_data):
    """Broadcast that a reporting effort was updated."""
    logger.info(f"📝 Broadcasting reporting_effort_updated: {reporting_effort_data.database_release_label}")
    logger.info(f"🔍 Active connections before broadcast: {len(manager.active_connections)}")
    # Convert SQLAlchemy model to Pydantic schema
    pydantic_reporting_effort = ReportingEffort.model_validate(reporting_effort_data)
    message = json.dumps({
        "type": "reporting_effort_updated",
        "data": pydantic_reporting_effort.model_dump()
    })
    await manager.broadcast(message)
    logger.info(f"✅ Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_reporting_effort_deleted(reporting_effort_id: int):
    """Broadcast that a reporting effort was deleted."""
    logger.info(f"🗑️ Broadcasting reporting_effort_deleted: ID {reporting_effort_id}")
    message = json.dumps({
        "type": "reporting_effort_deleted",
        "data": {"id": reporting_effort_id}
    })
    await manager.broadcast(message)
    logger.debug(f"✅ Broadcast completed to {len(manager.active_connections)} connections")