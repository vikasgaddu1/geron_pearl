"""WebSocket endpoint for real-time updates."""

import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import study, database_release, reporting_effort, text_element
from app.db.session import AsyncSessionLocal
from app.schemas.study import Study
from app.schemas.database_release import DatabaseRelease
from app.schemas.reporting_effort import ReportingEffort
from app.schemas.text_element import TextElement
from app.utils import sqlalchemy_to_dict, broadcast_message

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
                studies_json = [sqlalchemy_to_dict(s) for s in studies_data]
                message = broadcast_message("studies_update", studies_json)
                await manager.send_personal_message(message, websocket)
                logger.info(f"Sent initial data with {len(studies_json)} studies")
            except Exception as e:
                logger.error(f"Error sending initial data: {e}")
                message = broadcast_message("error", {"message": f"Error loading initial data: {str(e)}"})
                await manager.send_personal_message(message, websocket)
        
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
                    await manager.send_personal_message(json.dumps({"type": "ping"}), websocket)
                    continue
                message_data = json.loads(data)
                
                if message_data.get("action") == "refresh":
                    # Client requests data refresh
                    async with AsyncSessionLocal() as db:
                        try:
                            studies_data = await study.get_multi(db, skip=0, limit=100)
                            studies_json = [sqlalchemy_to_dict(s) for s in studies_data]
                            message = broadcast_message("studies_update", studies_json)
                            await manager.send_personal_message(message, websocket)
                            logger.info(f"Sent refresh data with {len(studies_json)} studies")
                        except Exception as e:
                            logger.error(f"Error during refresh: {e}")
                            message = broadcast_message("error", {"message": f"Error refreshing data: {str(e)}"})
                            await manager.send_personal_message(message, websocket)
                elif message_data.get("action") == "ping":
                    # Keep connection alive
                    await manager.send_personal_message(json.dumps({"type": "pong"}), websocket)
                    logger.info("Sent pong response")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                try:
                    message = broadcast_message("error", {"message": "Invalid JSON format"})
                    await manager.send_personal_message(message, websocket)
                except Exception:
                    logger.error("Failed to send error message, breaking loop")
                    break
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during message processing")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                try:
                    message = broadcast_message("error", {"message": "Error processing message"})
                    await manager.send_personal_message(message, websocket)
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
    logger.info(f"Broadcasting study_created: {study_data.study_label}")
    message = broadcast_message("study_created", sqlalchemy_to_dict(study_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_study_updated(study_data):
    """Broadcast that a study was updated."""
    logger.info(f"Broadcasting study_updated: {study_data.study_label}")
    message = broadcast_message("study_updated", sqlalchemy_to_dict(study_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_study_deleted(study_id: int):
    """Broadcast that a study was deleted."""
    logger.info(f"Broadcasting study_deleted: ID {study_id}")
    message = broadcast_message("study_deleted", {"id": study_id})
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_studies_refresh():
    """Broadcast a signal to refresh studies data."""
    message = json.dumps({"type": "refresh_needed"})
    await manager.broadcast(message)


async def broadcast_database_release_created(database_release_data):
    """Broadcast that a new database release was created."""
    logger.info(f"Broadcasting database_release_created: {database_release_data.database_release_label}")
    message = broadcast_message("database_release_created", sqlalchemy_to_dict(database_release_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_database_release_updated(database_release_data):
    """Broadcast that a database release was updated."""
    logger.info(f"Broadcasting database_release_updated: {database_release_data.database_release_label}")
    message = broadcast_message("database_release_updated", sqlalchemy_to_dict(database_release_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_database_release_deleted(database_release_id: int):
    """Broadcast that a database release was deleted."""
    logger.info(f"Broadcasting database_release_deleted: ID {database_release_id}")
    message = broadcast_message("database_release_deleted", {"id": database_release_id})
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_reporting_effort_created(reporting_effort_data):
    """Broadcast that a new reporting effort was created."""
    logger.info(f"Broadcasting reporting_effort_created: {reporting_effort_data.database_release_label}")
    message = broadcast_message("reporting_effort_created", sqlalchemy_to_dict(reporting_effort_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_reporting_effort_updated(reporting_effort_data):
    """Broadcast that a reporting effort was updated."""
    logger.info(f"Broadcasting reporting_effort_updated: {reporting_effort_data.database_release_label}")
    logger.info(f"Active connections before broadcast: {len(manager.active_connections)}")
    message = broadcast_message("reporting_effort_updated", sqlalchemy_to_dict(reporting_effort_data))
    await manager.broadcast(message)
    logger.info(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_reporting_effort_deleted(reporting_effort_id: int):
    """Broadcast that a reporting effort was deleted."""
    logger.info(f"Broadcasting reporting_effort_deleted: ID {reporting_effort_id}")
    message = broadcast_message("reporting_effort_deleted", {"id": reporting_effort_id})
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


# TextElement WebSocket broadcasting functions
async def broadcast_text_element_created(text_element_data):
    """Broadcast that a new text element was created."""
    logger.info(f"Broadcasting text_element_created: {text_element_data.type.value} - {text_element_data.label[:50]}...")
    message = broadcast_message("text_element_created", sqlalchemy_to_dict(text_element_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_text_element_updated(text_element_data):
    """Broadcast that a text element was updated."""
    logger.info(f"Broadcasting text_element_updated: {text_element_data.type.value} - {text_element_data.label[:50]}...")
    message = broadcast_message("text_element_updated", sqlalchemy_to_dict(text_element_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_text_element_deleted(text_element_data):
    """Broadcast that a text element was deleted."""
    logger.info(f"Broadcasting text_element_deleted: {text_element_data.type.value} - ID {text_element_data.id}")
    message = broadcast_message("text_element_deleted", sqlalchemy_to_dict(text_element_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


# Package WebSocket broadcasting functions
async def broadcast_package_created(package_data):
    """Broadcast that a new package was created."""
    logger.info(f"Broadcasting package_created: {package_data.package_name}")
    message = broadcast_message("package_created", sqlalchemy_to_dict(package_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_package_updated(package_data):
    """Broadcast that a package was updated."""
    logger.info(f"Broadcasting package_updated: {package_data.package_name}")
    message = broadcast_message("package_updated", sqlalchemy_to_dict(package_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_package_deleted(package_data):
    """Broadcast that a package was deleted."""
    logger.info(f"Broadcasting package_deleted: {package_data.package_name} - ID {package_data.id}")
    message = broadcast_message("package_deleted", sqlalchemy_to_dict(package_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


# PackageItem WebSocket broadcasting functions
async def broadcast_package_item_created(package_item_data):
    """Broadcast that a new package item was created."""
    logger.info(f"Broadcasting package_item_created: {package_item_data.item_code}")
    message = broadcast_message("package_item_created", sqlalchemy_to_dict(package_item_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


# Comment WebSocket broadcasting functions
async def broadcast_comment_created(comment_data):
    """Broadcast that a new comment was created."""
    logger.info(f"Broadcasting comment_created: tracker_id={comment_data.tracker_id}, type={comment_data.comment_type}")
    message = broadcast_message("comment_created", sqlalchemy_to_dict(comment_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_comment_updated(comment_data):
    """Broadcast that a comment was updated."""
    logger.info(f"Broadcasting comment_updated: comment_id={comment_data.id}, tracker_id={comment_data.tracker_id}")
    message = broadcast_message("comment_updated", sqlalchemy_to_dict(comment_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_comment_deleted(comment_data):
    """Broadcast that a comment was deleted."""
    logger.info(f"Broadcasting comment_deleted: comment_id={comment_data.id}, tracker_id={comment_data.tracker_id}")
    message = broadcast_message("comment_deleted", sqlalchemy_to_dict(comment_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_comment_resolved(comment_data):
    """Broadcast that a comment was resolved."""
    logger.info(f"Broadcasting comment_resolved: comment_id={comment_data.id}, tracker_id={comment_data.tracker_id}")
    message = broadcast_message("comment_resolved", sqlalchemy_to_dict(comment_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_package_item_updated(package_item_data):
    """Broadcast that a package item was updated."""
    logger.info(f"Broadcasting package_item_updated: {package_item_data.item_code}")
    message = broadcast_message("package_item_updated", sqlalchemy_to_dict(package_item_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_package_item_deleted(package_item_data):
    """Broadcast that a package item was deleted."""
    logger.info(f"Broadcasting package_item_deleted: {package_item_data.item_code} - ID {package_item_data.id}")
    message = broadcast_message("package_item_deleted", sqlalchemy_to_dict(package_item_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


# User WebSocket broadcasting functions
async def broadcast_user_created(user_data):
    """Broadcast that a new user was created."""
    logger.info(f"Broadcasting user_created: {user_data.username}")
    message = broadcast_message("user_created", sqlalchemy_to_dict(user_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_user_updated(user_data):
    """Broadcast that a user was updated."""
    logger.info(f"Broadcasting user_updated: {user_data.username}")
    message = broadcast_message("user_updated", sqlalchemy_to_dict(user_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_user_deleted(user_data):
    """Broadcast that a user was deleted."""
    logger.info(f"Broadcasting user_deleted: {user_data.username} - ID {user_data.id}")
    message = broadcast_message("user_deleted", sqlalchemy_to_dict(user_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


# Reporting Effort Tracker WebSocket broadcasting functions
async def broadcast_reporting_effort_item_created(item_data):
    """Broadcast that a new reporting effort item was created."""
    logger.info(f"Broadcasting reporting_effort_item_created: {item_data.item_code}")
    message = broadcast_message("reporting_effort_item_created", sqlalchemy_to_dict(item_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_reporting_effort_item_updated(item_data):
    """Broadcast that a reporting effort item was updated."""
    logger.info(f"Broadcasting reporting_effort_item_updated: {item_data.item_code}")
    message = broadcast_message("reporting_effort_item_updated", sqlalchemy_to_dict(item_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_reporting_effort_item_deleted(item_data):
    """Broadcast that a reporting effort item was deleted."""
    logger.info(f"Broadcasting reporting_effort_item_deleted: {item_data.item_code} - ID {item_data.id}")
    message = broadcast_message("reporting_effort_item_deleted", sqlalchemy_to_dict(item_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_reporting_effort_tracker_updated(tracker_data):
    """Broadcast that a reporting effort tracker was updated."""
    logger.info(f"Broadcasting reporting_effort_tracker_updated: ID {tracker_data.id}")
    message = broadcast_message("reporting_effort_tracker_updated", sqlalchemy_to_dict(tracker_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_tracker_assignment_updated(tracker_data, assignment_type, programmer_id):
    """Broadcast that a tracker assignment was updated."""
    logger.info(f"Broadcasting tracker_assignment_updated: {assignment_type} programmer {programmer_id} to tracker {tracker_data.id}")
    message = broadcast_message("tracker_assignment_updated", {
        "tracker": sqlalchemy_to_dict(tracker_data),
        "assignment_type": assignment_type,
        "programmer_id": programmer_id
    })
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_tracker_comment_created(comment_data):
    """Broadcast that a new tracker comment was created."""
    logger.info(f"Broadcasting tracker_comment_created: ID {comment_data.id}")
    message = broadcast_message("tracker_comment_created", sqlalchemy_to_dict(comment_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_tracker_comment_updated(comment_data):
    """Broadcast that a tracker comment was updated."""
    logger.info(f"Broadcasting tracker_comment_updated: ID {comment_data.id}")
    message = broadcast_message("tracker_comment_updated", sqlalchemy_to_dict(comment_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_tracker_comment_deleted(comment_data):
    """Broadcast that a tracker comment was deleted."""
    logger.info(f"Broadcasting tracker_comment_deleted: ID {comment_data.id}")
    message = broadcast_message("tracker_comment_deleted", sqlalchemy_to_dict(comment_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_reporting_effort_tracker_deleted(tracker_data):
    """Broadcast that a reporting effort tracker was deleted."""
    logger.info(f"Broadcasting reporting_effort_tracker_deleted: ID {tracker_data.id}")
    message = broadcast_message("reporting_effort_tracker_deleted", sqlalchemy_to_dict(tracker_data))
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


# Simplified comment system WebSocket functions
async def broadcast_comment_created(tracker_id: int, comment_data, unresolved_count: int):
    """Broadcast that a new comment was created (parent comment)."""
    logger.info(f"Broadcasting comment_created: tracker_id={tracker_id}, unresolved_count={unresolved_count}")
    
    # Convert CommentWithUserInfo to dict for broadcasting
    if hasattr(comment_data, 'model_dump'):
        comment_dict = comment_data.model_dump(mode='json')
    else:
        comment_dict = comment_data if isinstance(comment_data, dict) else sqlalchemy_to_dict(comment_data)
    
    message = broadcast_message("comment_created", {
        "tracker_id": tracker_id,
        "comment": comment_dict,
        "unresolved_count": unresolved_count
    })
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_comment_replied(tracker_id: int, parent_comment_id: int, comment_data, unresolved_count: int):
    """Broadcast that a reply was added to a comment."""
    logger.info(f"Broadcasting comment_replied: tracker_id={tracker_id}, parent_comment_id={parent_comment_id}")
    
    # Convert CommentWithUserInfo to dict for broadcasting
    if hasattr(comment_data, 'model_dump'):
        comment_dict = comment_data.model_dump(mode='json')
    else:
        comment_dict = comment_data if isinstance(comment_data, dict) else sqlalchemy_to_dict(comment_data)
    
    message = broadcast_message("comment_replied", {
        "tracker_id": tracker_id,
        "parent_comment_id": parent_comment_id,
        "reply": comment_dict,
        "unresolved_count": unresolved_count
    })
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")


async def broadcast_comment_resolved(tracker_id: int, comment_id: int, unresolved_count: int):
    """Broadcast that a comment was resolved."""
    logger.info(f"Broadcasting comment_resolved: tracker_id={tracker_id}, comment_id={comment_id}, unresolved_count={unresolved_count}")
    message = broadcast_message("comment_resolved", {
        "tracker_id": tracker_id,
        "comment_id": comment_id,
        "unresolved_count": unresolved_count
    })
    await manager.broadcast(message)
    logger.debug(f"Broadcast completed to {len(manager.active_connections)} connections")
