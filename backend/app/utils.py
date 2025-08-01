import json
from datetime import datetime, date
from enum import Enum

def json_serializer(obj):
    """
    Custom JSON serializer for objects not serializable by default json code.
    Handles datetime, date, and enum objects.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")

def sqlalchemy_to_dict(model_instance):
    """
    Convert a SQLAlchemy model instance to a dictionary, ready for JSON serialization.
    """
    if model_instance is None:
        return None
    
    d = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        if isinstance(value, (datetime, date)):
            d[column.name] = value.isoformat()
        elif isinstance(value, Enum):
            d[column.name] = value.value
        else:
            d[column.name] = value
    return d

def broadcast_message(message_type: str, data: dict):
    """
    Constructs a JSON message for broadcasting.
    """
    return json.dumps({
        "type": message_type,
        "data": data
    }, default=json_serializer)
