"""System endpoints for health checks, version info, and tenant status."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    version: str
    timestamp: str


class VersionResponse(BaseModel):
    """Version info response."""

    version: str
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    license_valid: bool
    environment: str


class TenantInfoResponse(BaseModel):
    """Tenant information response."""

    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    is_multi_tenant: bool
    license_key_configured: bool


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Check system health including database connectivity.

    This endpoint is used by:
    - Load balancers for health checks
    - Monitoring systems
    - The central tenant registry for health monitoring
    """
    # Check database connectivity
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        database=db_status,
        tenant_id=settings.tenant_id,
        tenant_name=settings.tenant_name,
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/version", response_model=VersionResponse)
async def version_info() -> VersionResponse:
    """
    Get version and license information.

    Used by:
    - Update checker to determine if updates are available
    - License validation
    - Debugging deployment issues
    """
    # Simple license check - in production this would validate against central server
    license_valid = True  # Soft enforcement - always valid, show warnings elsewhere

    return VersionResponse(
        version=settings.app_version,
        tenant_id=settings.tenant_id,
        tenant_name=settings.tenant_name,
        license_valid=license_valid,
        environment=settings.env,
    )


@router.get("/tenant", response_model=TenantInfoResponse)
async def tenant_info() -> TenantInfoResponse:
    """
    Get tenant configuration information.

    Used by:
    - Frontend to display tenant branding
    - Determining if this is a multi-tenant deployment
    """
    return TenantInfoResponse(
        tenant_id=settings.tenant_id,
        tenant_name=settings.tenant_name,
        is_multi_tenant=settings.tenant_id is not None,
        license_key_configured=settings.license_key is not None,
    )
