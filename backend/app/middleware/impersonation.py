"""Impersonation middleware for read-only enforcement.

This middleware checks if the request is from a super admin impersonation
session in read-only mode and blocks mutation requests.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError

logger = logging.getLogger(__name__)

# HTTP methods that modify data
MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Endpoints that are always allowed (super admin exit, etc.)
ALLOWED_ENDPOINTS = {
    "/api/v1/super-admin/impersonate/end",
    "/api/v1/auth/logout",
}


class ImpersonationReadOnlyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce read-only mode for impersonation sessions.
    
    When a super admin is impersonating a tenant user with read_only=True,
    this middleware blocks all mutation requests (POST, PUT, PATCH, DELETE).
    """
    
    async def dispatch(self, request: Request, call_next):
        # Only check mutation methods
        if request.method not in MUTATION_METHODS:
            return await call_next(request)
        
        # Skip certain endpoints
        if request.url.path in ALLOWED_ENDPOINTS:
            return await call_next(request)
        
        # Check for impersonation token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Try to decode as impersonation token
        try:
            from app.core.super_admin_security import (
                decode_impersonation_token,
                SUPER_ADMIN_JWT_SECRET,
            )
            
            payload = decode_impersonation_token(token)
            
            # Check if read-only mode
            if payload.get("read_only", True):
                super_admin_id = payload.get("super_admin_id", "unknown")
                logger.warning(
                    f"Read-only impersonation blocked {request.method} {request.url.path} "
                    f"(super_admin_id={super_admin_id})"
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "detail": "Read-only impersonation mode - mutations are blocked. "
                                  "Exit impersonation to make changes."
                    }
                )
        except JWTError:
            # Not an impersonation token, let it through
            pass
        except Exception as e:
            # Unexpected error - log but don't block
            logger.debug(f"Impersonation check error: {e}")
        
        return await call_next(request)
