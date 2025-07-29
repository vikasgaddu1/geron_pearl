"""Security utilities and dependencies."""

from typing import Optional

from fastapi import HTTPException, status


def get_current_user() -> dict:
    """
    Get current authenticated user.
    This is a placeholder for future OAuth2/JWT implementation.
    """
    # TODO: Implement OAuth2/JWT authentication
    return {"id": 1, "username": "dev_user"}


def verify_api_key(api_key: Optional[str] = None) -> bool:
    """
    Verify API key for authentication.
    This is a placeholder for future API key authentication.
    """
    # TODO: Implement API key verification
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    return True