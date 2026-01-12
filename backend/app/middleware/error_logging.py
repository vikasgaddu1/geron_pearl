"""Middleware for automatic error logging."""

import traceback
import uuid
import json
import logging
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from jose import jwt, JWTError

from app.db.session import AsyncSessionLocal
from app.crud.error_log import error_log
from app.core.config import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


def extract_user_id_from_token(request: Request) -> Optional[int]:
    """Extract user ID from JWT token in Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]  # Remove "Bearer " prefix
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        user_id_str = payload.get("sub")
        if user_id_str:
            return int(user_id_str)
    except (JWTError, ValueError):
        pass
    return None


def sanitize_body(body: bytes) -> Optional[str]:
    """Remove sensitive fields from request body."""
    if not body:
        return None
    try:
        data = json.loads(body.decode('utf-8'))
        # Remove sensitive fields
        sensitive_keys = [
            'password', 'token', 'secret', 'api_key', 'refresh_token',
            'access_token', 'password_hash', 'new_password', 'current_password'
        ]
        for key in list(data.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                data[key] = '[REDACTED]'
        return json.dumps(data)[:5000]  # Limit size
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def get_correlation_id(request: Request) -> str:
    """Get or generate correlation ID."""
    return request.headers.get('X-Correlation-ID', str(uuid.uuid4()))


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to capture and log errors to database."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = get_correlation_id(request)
        request.state.correlation_id = correlation_id

        # Store request body for potential error logging
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                # Reset the body for downstream processing
                request._body = body
            except Exception:
                pass

        try:
            response = await call_next(request)

            # Log 5xx errors (server errors) that were handled but returned error status
            if response.status_code >= 500:
                await self._log_error(
                    request=request,
                    error_type="HTTPError",
                    message=f"Server error: {response.status_code}",
                    severity="ERROR",
                    response_status=response.status_code,
                    correlation_id=correlation_id,
                    body=body
                )

            return response

        except Exception as exc:
            # Log unhandled exceptions
            await self._log_error(
                request=request,
                error_type=type(exc).__name__,
                message=str(exc)[:2000],
                stack_trace=traceback.format_exc(),
                severity="CRITICAL",
                response_status=500,
                correlation_id=correlation_id,
                body=body
            )
            raise

    async def _log_error(
        self,
        request: Request,
        error_type: str,
        message: str,
        severity: str,
        response_status: int,
        correlation_id: str,
        stack_trace: Optional[str] = None,
        body: Optional[bytes] = None
    ):
        """Log error to database (best-effort)."""
        try:
            # Extract user ID from JWT token in Authorization header
            user_id = extract_user_id_from_token(request)

            # Sanitize request body
            sanitized_body = sanitize_body(body) if body else None

            async with AsyncSessionLocal() as db:
                await error_log.log_error(
                    db,
                    source="BACKEND",
                    severity=severity,
                    error_type=error_type,
                    message=message[:2000],
                    stack_trace=stack_trace[:10000] if stack_trace else None,
                    request_method=request.method,
                    request_path=str(request.url.path)[:500],
                    request_body=sanitized_body,
                    response_status=response_status,
                    user_id=user_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    correlation_id=correlation_id
                )
        except Exception as e:
            # Error logging is best-effort - don't crash the app
            logger.error(f"Failed to log error to database: {e}")
