"""Tenant data management endpoints.

This module provides endpoints for:
- Marking onboarding as complete
- GDPR data export
- Backup and restore
- Rate limit status
"""

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.tenant_settings import TenantSettings, DEFAULT_TENANT_SETTINGS
from app.services.data_export import export_tenant_data, export_tenant_data_as_zip
from app.services.backup_restore import (
    create_tenant_backup,
    create_tenant_backup_zip,
    restore_tenant_backup,
)
from app.core.rate_limiting import get_tenant_usage, get_tenant_limits

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Onboarding Endpoints
# =============================================================================

class OnboardingStatus(BaseModel):
    """Onboarding status for a tenant."""
    onboarding_completed: bool
    tenant_id: int


@router.get("/onboarding/status", response_model=OnboardingStatus)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get onboarding status for the current tenant.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return OnboardingStatus(
        onboarding_completed=tenant.onboarding_completed,
        tenant_id=tenant.id,
    )


@router.post("/onboarding/complete")
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Mark onboarding as complete for the current tenant.
    """
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    tenant.onboarding_completed = True
    await db.commit()

    logger.info(f"Onboarding completed for tenant {tenant.id} by user {current_user.id}")

    return {"message": "Onboarding completed", "tenant_id": tenant.id}


# =============================================================================
# GDPR Data Export Endpoints
# =============================================================================

@router.get("/export-data")
async def export_data(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Export all tenant data (GDPR compliance).

    Returns a JSON file containing all tenant data including:
    - Users
    - Studies and hierarchy
    - Packages and items
    - Text elements
    - Audit logs (last 90 days)
    - Notifications (last 30 days)

    Admin only.
    """
    try:
        data = await export_tenant_data(db, current_user.tenant_id)

        logger.info(f"Data export requested for tenant {current_user.tenant_id} by user {current_user.id}")

        # Return as downloadable JSON file
        json_content = json.dumps(data, indent=2, ensure_ascii=False)

        return StreamingResponse(
            BytesIO(json_content.encode('utf-8')),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=pearl_export_{current_user.tenant_id}.json"
            }
        )

    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}",
        )


@router.get("/export-data/zip")
async def export_data_zip(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Export all tenant data as a ZIP file (GDPR compliance).

    Returns a ZIP file containing:
    - data.json: Complete tenant data
    - metadata.json: Export metadata

    Admin only.
    """
    try:
        zip_content = await export_tenant_data_as_zip(db, current_user.tenant_id)

        logger.info(f"ZIP data export for tenant {current_user.tenant_id} by user {current_user.id}")

        return StreamingResponse(
            BytesIO(zip_content),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=pearl_export_{current_user.tenant_id}.zip"
            }
        )

    except Exception as e:
        logger.error(f"Failed to export data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}",
        )


# =============================================================================
# Backup and Restore Endpoints
# =============================================================================

class BackupStats(BaseModel):
    """Statistics from backup restoration."""
    studies_created: int
    database_releases_created: int
    reporting_efforts_created: int
    packages_created: int
    package_items_created: int
    text_elements_created: int


class RestoreRequest(BaseModel):
    """Request body for restore operation."""
    clear_existing: bool = False


@router.get("/backup")
async def create_backup(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a backup of all tenant data.

    Returns a JSON file that can be used to restore data.

    Admin only.
    """
    try:
        data = await create_tenant_backup(db, current_user.tenant_id)

        logger.info(f"Backup created for tenant {current_user.tenant_id} by user {current_user.id}")

        json_content = json.dumps(data, indent=2, ensure_ascii=False)

        return StreamingResponse(
            BytesIO(json_content.encode('utf-8')),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=pearl_backup_{current_user.tenant_id}.json"
            }
        )

    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}",
        )


@router.get("/backup/zip")
async def create_backup_zip(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Create a ZIP backup of all tenant data.

    Admin only.
    """
    try:
        zip_content = await create_tenant_backup_zip(db, current_user.tenant_id)

        logger.info(f"ZIP backup created for tenant {current_user.tenant_id} by user {current_user.id}")

        return StreamingResponse(
            BytesIO(zip_content),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=pearl_backup_{current_user.tenant_id}.zip"
            }
        )

    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}",
        )


@router.post("/restore", response_model=BackupStats)
async def restore_from_backup(
    file: UploadFile = File(...),
    clear_existing: bool = False,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Restore tenant data from a backup file.

    Upload a JSON backup file to restore data.

    Parameters:
    - file: The backup JSON file
    - clear_existing: If true, clears existing data before restore

    Admin only.
    """
    try:
        # Read and parse the backup file
        content = await file.read()
        backup_data = json.loads(content.decode('utf-8'))

        # Restore from backup
        stats = await restore_tenant_backup(
            db,
            tenant_id=current_user.tenant_id,
            backup_data=backup_data,
            clear_existing=clear_existing,
            admin_user_id=current_user.id,
        )

        logger.info(f"Backup restored for tenant {current_user.tenant_id} by user {current_user.id}: {stats}")

        return BackupStats(**stats)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON file",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore backup: {str(e)}",
        )


# =============================================================================
# Rate Limiting and Usage Endpoints
# =============================================================================

class UsageStats(BaseModel):
    """Current API usage statistics."""
    requests_last_minute: int
    requests_last_hour: int
    requests_last_day: int
    concurrent_requests: int


class RateLimits(BaseModel):
    """Rate limits for current plan."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    max_concurrent_requests: int


class UsageResponse(BaseModel):
    """Usage and limits response."""
    usage: UsageStats
    limits: RateLimits
    plan_name: Optional[str] = None


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get current API usage statistics and rate limits.
    """
    # Get tenant's plan
    result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    plan_name = None
    if tenant and tenant.subscription_plan_id:
        from app.models.subscription_plan import SubscriptionPlan
        plan_result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == tenant.subscription_plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if plan:
            plan_name = plan.name

    # Get usage and limits
    usage = get_tenant_usage(current_user.tenant_id)
    limits = get_tenant_limits(plan_name)

    return UsageResponse(
        usage=UsageStats(**usage),
        limits=RateLimits(**limits),
        plan_name=plan_name,
    )


# =============================================================================
# Tenant Settings Endpoints
# =============================================================================

class SignatureLockSettingResponse(BaseModel):
    """Response for signature lock setting."""
    signature_locks_effort: bool


class SignatureLockSettingUpdate(BaseModel):
    """Request body to update signature lock setting."""
    signature_locks_effort: bool


@router.get("/settings/signature-locks-effort", response_model=SignatureLockSettingResponse)
async def get_signature_lock_setting(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get the signature lock setting for the current tenant.
    
    When True (default): Signing automatically locks the effort, manual lock/unlock is hidden.
    When False: Lock/unlock is manual and independent of signing (no TOTP required for locking).
    """
    result = await db.execute(
        select(Tenant).options(selectinload(Tenant.settings)).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Return setting from tenant settings, or default if not set
    signature_locks_effort = True  # Default
    if tenant.settings:
        signature_locks_effort = tenant.settings.signature_locks_effort

    return SignatureLockSettingResponse(signature_locks_effort=signature_locks_effort)


@router.put("/settings/signature-locks-effort", response_model=SignatureLockSettingResponse)
async def update_signature_lock_setting(
    setting: SignatureLockSettingUpdate,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Update the signature lock setting for the current tenant.
    
    Admin only.
    
    When True: Signing automatically locks the effort, manual lock/unlock is hidden.
    When False: Lock/unlock is manual and independent of signing.
    """
    result = await db.execute(
        select(Tenant).options(selectinload(Tenant.settings)).where(Tenant.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Create settings if they don't exist
    if not tenant.settings:
        tenant_settings = TenantSettings(
            tenant_id=tenant.id,
            **DEFAULT_TENANT_SETTINGS
        )
        tenant_settings.signature_locks_effort = setting.signature_locks_effort
        db.add(tenant_settings)
    else:
        tenant.settings.signature_locks_effort = setting.signature_locks_effort

    await db.commit()

    logger.info(
        f"Signature lock setting updated to {setting.signature_locks_effort} "
        f"for tenant {tenant.id} by user {current_user.id}"
    )

    return SignatureLockSettingResponse(signature_locks_effort=setting.signature_locks_effort)
