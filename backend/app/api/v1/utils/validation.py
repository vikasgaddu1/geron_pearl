"""Utilities for validation and error handling."""

from typing import Any, Dict
from functools import wraps
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError


def handle_validation_error(func):
    """Decorator to handle common validation errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error: {str(e)}"
            )
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database constraint violation: {str(e.orig)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )
    return wrapper


def format_validation_error(error: ValidationError) -> Dict[str, Any]:
    """Format Pydantic validation error for API response."""
    formatted_errors = []
    for err in error.errors():
        formatted_errors.append({
            "field": ".".join(str(x) for x in err["loc"]),
            "message": err["msg"],
            "type": err["type"]
        })
    
    return {
        "message": "Validation failed",
        "errors": formatted_errors
    }


def format_integrity_error(error: IntegrityError) -> Dict[str, Any]:
    """Format SQLAlchemy integrity error for API response."""
    error_msg = str(error.orig)
    
    # Handle common constraint violations
    if "UNIQUE constraint failed" in error_msg:
        return {"message": "A record with this value already exists"}
    elif "NOT NULL constraint failed" in error_msg:
        return {"message": "Required field is missing"}
    elif "FOREIGN KEY constraint failed" in error_msg:
        return {"message": "Referenced record does not exist"}
    else:
        return {"message": f"Database constraint violation: {error_msg}"}


class ValidationError(Exception):
    """Custom validation error for business logic validation."""
    
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_required_field(value: Any, field_name: str) -> None:
    """Validate that a required field is not None or empty."""
    if value is None:
        raise ValidationError(f"{field_name} is required", field_name)
    
    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"{field_name} cannot be empty", field_name)


def validate_string_length(value: str, field_name: str, min_length: int = 1, max_length: int = 255) -> None:
    """Validate string length constraints."""
    if value is None:
        return
    
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters long", field_name)
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} must be no more than {max_length} characters long", field_name)


def validate_positive_integer(value: int, field_name: str) -> None:
    """Validate that an integer is positive."""
    if value is None:
        return
    
    if not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field_name} must be a positive integer", field_name)


def normalize_label(label: str) -> str:
    """Normalize label for duplicate checking (remove spaces, convert to uppercase)."""
    if not label:
        return ""
    return label.replace(" ", "").upper()


def check_duplicate_label(existing_labels: list, new_label: str, entity_type: str = "entity") -> None:
    """Check for duplicate labels using normalized comparison."""
    normalized_new = normalize_label(new_label)
    
    for existing_label in existing_labels:
        if normalize_label(existing_label) == normalized_new:
            raise ValidationError(
                f"A {entity_type} with similar content already exists: '{existing_label}'. "
                f"Duplicate {entity_type}s are not allowed (comparison ignores spaces and case).",
                "label"
            )