"""Utilities for WebSocket broadcasting."""

import json
from typing import Any, Dict, Optional, Union
from enum import Enum
from datetime import datetime
from app.api.v1.websocket import manager


def json_serializer(obj: Any) -> Any:
    """JSON serializer for WebSocket messages that handles SQLAlchemy models and special types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return obj.value
    elif hasattr(obj, '__dict__'):
        # Handle SQLAlchemy models by converting to dict
        return {key: json_serializer(value) for key, value in obj.__dict__.items() if not key.startswith('_')}
    else:
        return obj


def sqlalchemy_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert SQLAlchemy model to dictionary with proper serialization."""
    if obj is None:
        return {}
    
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            result[column.name] = value.isoformat()
        elif isinstance(value, Enum):
            result[column.name] = value.value
        else:
            result[column.name] = value
    
    return result


async def broadcast_entity_change(
    entity_type: str,
    action: str,
    entity_data: Union[Dict[str, Any], Any],
    entity_id: Optional[int] = None
) -> None:
    """
    Generic function to broadcast entity changes via WebSocket.
    
    Args:
        entity_type: Type of entity (e.g., 'study', 'package', 'user')
        action: Action performed (e.g., 'created', 'updated', 'deleted')
        entity_data: Entity data (dict or SQLAlchemy model)
        entity_id: Optional entity ID for delete operations
    """
    try:
        # Convert SQLAlchemy model to dict if needed
        if hasattr(entity_data, '__table__'):
            data = sqlalchemy_to_dict(entity_data)
        elif isinstance(entity_data, dict):
            data = entity_data
        else:
            # Try to serialize with json_serializer
            data = json_serializer(entity_data)

        # For delete operations, ensure we have the ID
        if action == 'deleted' and entity_id:
            data = {'id': entity_id} if not data else {**data, 'id': entity_id}

        message = {
            'type': f'{entity_type}_{action}',
            'data': data
        }
        
        # Broadcast to all connected WebSocket clients
        await manager.broadcast_json(message)
        
    except Exception as e:
        # Log error but don't raise to avoid breaking API operations
        print(f"WebSocket broadcast error for {entity_type}_{action}: {str(e)}")


# Specific broadcast functions for common entities
async def broadcast_study_created(study_data: Any) -> None:
    """Broadcast study creation."""
    await broadcast_entity_change('study', 'created', study_data)


async def broadcast_study_updated(study_data: Any) -> None:
    """Broadcast study update."""
    await broadcast_entity_change('study', 'updated', study_data)


async def broadcast_study_deleted(study_id: int) -> None:
    """Broadcast study deletion."""
    await broadcast_entity_change('study', 'deleted', {}, study_id)


async def broadcast_package_created(package_data: Any) -> None:
    """Broadcast package creation."""
    await broadcast_entity_change('package', 'created', package_data)


async def broadcast_package_updated(package_data: Any) -> None:
    """Broadcast package update."""
    await broadcast_entity_change('package', 'updated', package_data)


async def broadcast_package_deleted(package_id: int) -> None:
    """Broadcast package deletion."""
    await broadcast_entity_change('package', 'deleted', {}, package_id)


async def broadcast_user_created(user_data: Any) -> None:
    """Broadcast user creation."""
    await broadcast_entity_change('user', 'created', user_data)


async def broadcast_user_updated(user_data: Any) -> None:
    """Broadcast user update."""
    await broadcast_entity_change('user', 'updated', user_data)


async def broadcast_user_deleted(user_id: int) -> None:
    """Broadcast user deletion."""
    await broadcast_entity_change('user', 'deleted', {}, user_id)


async def broadcast_text_element_created(text_element_data: Any) -> None:
    """Broadcast text element creation."""
    await broadcast_entity_change('text_element', 'created', text_element_data)


async def broadcast_text_element_updated(text_element_data: Any) -> None:
    """Broadcast text element update."""
    await broadcast_entity_change('text_element', 'updated', text_element_data)


async def broadcast_text_element_deleted(text_element_id: int) -> None:
    """Broadcast text element deletion."""
    await broadcast_entity_change('text_element', 'deleted', {}, text_element_id)