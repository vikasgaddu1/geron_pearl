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


# =============================================================================
# PYDANTIC MODEL CONVERSION PATTERNS (Phase 2B - Medium Priority)
# =============================================================================

def convert_sqlalchemy_to_pydantic(sqlalchemy_obj: Any, pydantic_model: Any) -> Any:
    """
    Convert SQLAlchemy model instance to Pydantic model with error handling.
    
    Args:
        sqlalchemy_obj: SQLAlchemy model instance
        pydantic_model: Pydantic model class
        
    Returns:
        Pydantic model instance
    """
    try:
        return pydantic_model.model_validate(sqlalchemy_obj)
    except Exception as e:
        print(f"Error converting {type(sqlalchemy_obj)} to {pydantic_model}: {str(e)}")
        raise


def serialize_for_websocket(pydantic_obj: Any, exclude_fields: list = None, mode: str = 'json') -> Dict[str, Any]:
    """
    Serialize Pydantic model for WebSocket transmission with field exclusion support.
    
    Args:
        pydantic_obj: Pydantic model instance
        exclude_fields: List of field names to exclude from serialization
        mode: Serialization mode ('json' handles enums and dates properly)
        
    Returns:
        Dictionary suitable for JSON serialization
    """
    try:
        exclude_set = set(exclude_fields) if exclude_fields else set()
        return pydantic_obj.model_dump(mode=mode, exclude=exclude_set)
    except Exception as e:
        print(f"Error serializing {type(pydantic_obj)} for WebSocket: {str(e)}")
        # Fallback to basic dict conversion
        return sqlalchemy_to_dict(pydantic_obj) if hasattr(pydantic_obj, '__table__') else {}


def batch_convert_models(sqlalchemy_list: list, pydantic_model: Any, exclude_fields: list = None) -> list:
    """
    Convert list of SQLAlchemy models to Pydantic models and serialize for WebSocket.
    
    Args:
        sqlalchemy_list: List of SQLAlchemy model instances
        pydantic_model: Pydantic model class
        exclude_fields: Fields to exclude from serialization
        
    Returns:
        List of serialized dictionaries
    """
    results = []
    for item in sqlalchemy_list:
        try:
            pydantic_obj = convert_sqlalchemy_to_pydantic(item, pydantic_model)
            serialized = serialize_for_websocket(pydantic_obj, exclude_fields)
            results.append(serialized)
        except Exception as e:
            print(f"Error in batch conversion for item {getattr(item, 'id', 'unknown')}: {str(e)}")
            # Continue with other items, don't break the entire batch
            continue
    
    return results


def safe_model_conversion(sqlalchemy_obj: Any, pydantic_model: Any, default: Any = None) -> Any:
    """
    Safely convert SQLAlchemy to Pydantic model with fallback default.
    
    Args:
        sqlalchemy_obj: SQLAlchemy model instance  
        pydantic_model: Pydantic model class
        default: Default value to return on conversion failure
        
    Returns:
        Pydantic model instance or default value
    """
    try:
        return convert_sqlalchemy_to_pydantic(sqlalchemy_obj, pydantic_model)
    except Exception as e:
        print(f"Safe conversion failed for {type(sqlalchemy_obj)}: {str(e)}")
        return default


def create_websocket_response(data: Any, message_type: str, pydantic_model: Any = None) -> Dict[str, Any]:
    """
    Create standardized WebSocket response with proper model conversion.
    
    Args:
        data: Data to include (SQLAlchemy model, Pydantic model, or dict)
        message_type: WebSocket message type
        pydantic_model: Optional Pydantic model for conversion
        
    Returns:
        Dictionary ready for WebSocket broadcasting
    """
    try:
        # Convert to Pydantic if SQLAlchemy model and Pydantic model provided
        if hasattr(data, '__table__') and pydantic_model:
            data = convert_sqlalchemy_to_pydantic(data, pydantic_model)
        
        # Serialize for WebSocket
        if hasattr(data, 'model_dump'):
            serialized_data = serialize_for_websocket(data)
        elif isinstance(data, dict):
            serialized_data = data
        else:
            serialized_data = json_serializer(data)
        
        return {
            'type': message_type,
            'data': serialized_data,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error creating WebSocket response for {message_type}: {str(e)}")
        return {
            'type': message_type,
            'data': {},
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }