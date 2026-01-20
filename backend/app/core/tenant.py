"""Tenant context management for multi-tenancy.

This module provides utilities for managing tenant context in a multi-tenant environment.
The tenant context is extracted from the JWT token and used to:
1. Set PostgreSQL session variables for Row-Level Security (RLS)
2. Filter queries to the current tenant's data
"""

from contextvars import ContextVar
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import decode_token


# Context variable for storing current tenant ID
current_tenant_id: ContextVar[Optional[int]] = ContextVar('current_tenant_id', default=None)


def get_tenant_id_from_token(request: Request) -> Optional[int]:
    """
    Extract tenant_id from JWT token in request headers.
    
    Returns None if no token present or token is invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    
    try:
        token = auth_header.replace("Bearer ", "")
        payload = decode_token(token)
        return payload.get("tenant_id")
    except Exception:
        return None


async def set_tenant_context_for_request(
    db: AsyncSession,
    tenant_id: Optional[int]
) -> None:
    """
    Set PostgreSQL session variable for RLS.
    
    Uses SET LOCAL to scope the setting to the current transaction,
    which is safe with connection pooling.
    
    Args:
        db: Database session
        tenant_id: Tenant ID to set, or None/0 for super admin bypass
    """
    if tenant_id and tenant_id > 0:
        # Regular tenant - set the tenant_id for RLS
        await db.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))
    else:
        # Super admin or no tenant - set to 0 for bypass
        # Note: Super admin connections should use BYPASSRLS role instead
        await db.execute(text("SET LOCAL app.current_tenant_id = '0'"))


async def get_current_tenant_id_from_request(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> int:
    """
    FastAPI dependency to get and validate current tenant ID.
    
    Sets the tenant context in PostgreSQL and returns the tenant ID.
    Raises 401 if no valid tenant context is available.
    """
    tenant_id = get_tenant_id_from_token(request)
    
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No tenant context available. Please authenticate.",
        )
    
    # Store in context variable for use in other parts of the request
    current_tenant_id.set(tenant_id)
    
    # Set in PostgreSQL for RLS
    await set_tenant_context_for_request(db, tenant_id)
    
    return tenant_id


async def get_optional_tenant_id(
    request: Request,
) -> Optional[int]:
    """
    FastAPI dependency to optionally get tenant ID.
    
    Returns None if no tenant context is available (for public endpoints).
    """
    return get_tenant_id_from_token(request)


def require_tenant_context():
    """
    Decorator/dependency factory to require tenant context.
    
    Use this for endpoints that require tenant isolation.
    """
    async def dependency(
        tenant_id: int = Depends(get_current_tenant_id_from_request)
    ) -> int:
        return tenant_id
    
    return dependency


async def verify_tenant_access(
    db: AsyncSession,
    tenant_id: int,
    resource_tenant_id: int
) -> bool:
    """
    Verify that the current tenant has access to a resource.
    
    Args:
        db: Database session
        tenant_id: Current tenant ID from context
        resource_tenant_id: Tenant ID of the resource being accessed
    
    Returns:
        True if access is allowed, False otherwise
    """
    # Simple check - tenant can only access their own resources
    # Super admin (tenant_id = 0) can access all resources
    if tenant_id == 0:
        return True
    return tenant_id == resource_tenant_id


class TenantContextMiddleware:
    """
    ASGI middleware to extract and store tenant context.
    
    This middleware runs on every request and extracts the tenant ID
    from the JWT token, storing it in a context variable for later use.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract tenant ID from headers
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            
            tenant_id = None
            if auth_header.startswith("Bearer "):
                try:
                    token = auth_header.replace("Bearer ", "")
                    payload = decode_token(token)
                    tenant_id = payload.get("tenant_id")
                except Exception:
                    pass
            
            # Store in context variable
            token = current_tenant_id.set(tenant_id)
            try:
                await self.app(scope, receive, send)
            finally:
                current_tenant_id.reset(token)
        else:
            await self.app(scope, receive, send)


def get_current_tenant() -> Optional[int]:
    """
    Get the current tenant ID from context variable.
    
    This can be called from anywhere in the request lifecycle
    after the middleware has run.
    """
    return current_tenant_id.get()
