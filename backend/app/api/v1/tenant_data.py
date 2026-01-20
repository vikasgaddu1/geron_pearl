"""Tenant data management endpoints.

This module provides endpoints for:
- Resetting tenant data to sample state
- Checking sample data status
- Seeding sample data on demand
- Marking onboarding as complete
- GDPR data export
- Backup and restore
- Rate limit status
"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from app.core.security import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.services.sample_data import (
    seed_sample_data,
    clear_tenant_data,
    reset_to_sample_data,
    check_has_sample_data,
)
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
# Response Schemas
# =============================================================================

class SampleDataStatus(BaseModel):
    """Status of sample data for a tenant."""
    has_sample_data: bool
    tenant_id: int


class DataCounts(BaseModel):
    """Counts of entities in various operations."""
    studies: int
    database_releases: int = 0
    packages: int
    package_items: int = 0
    text_elements: int
    users: int = 0


class ResetResponse(BaseModel):
    """Response for data reset operation."""
    message: str
    cleared: DataCounts
    seeded: DataCounts


class SeedResponse(BaseModel):
    """Response for data seeding operation."""
    message: str
    counts: DataCounts


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/sample-data/status", response_model=SampleDataStatus)
async def get_sample_data_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Check if the current tenant has sample data seeded.
    """
    has_sample = await check_has_sample_data(db, current_user.tenant_id)
    
    return SampleDataStatus(
        has_sample_data=has_sample,
        tenant_id=current_user.tenant_id,
    )


@router.post("/sample-data/seed", response_model=SeedResponse)
async def seed_sample_data_endpoint(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Seed sample data for the current tenant.
    
    Admin only. Will fail if sample data already exists.
    """
    # Check if sample data already exists
    if await check_has_sample_data(db, current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sample data already exists. Use reset endpoint to clear and re-seed.",
        )
    
    try:
        counts = await seed_sample_data(
            db,
            tenant_id=current_user.tenant_id,
            admin_user_id=current_user.id,
        )
        
        logger.info(f"Sample data seeded for tenant {current_user.tenant_id} by user {current_user.id}")
        
        return SeedResponse(
            message="Sample data seeded successfully",
            counts=DataCounts(**counts),
        )
        
    except Exception as e:
        logger.error(f"Failed to seed sample data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed sample data: {str(e)}",
        )


@router.post("/reset-to-sample", response_model=ResetResponse)
async def reset_to_sample_data_endpoint(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Reset tenant data to sample state.
    
    WARNING: This will delete ALL existing data (except users) and replace
    it with sample data. This action cannot be undone.
    
    Admin only.
    """
    try:
        result = await reset_to_sample_data(
            db,
            tenant_id=current_user.tenant_id,
            admin_user_id=current_user.id,
        )
        
        logger.info(f"Tenant {current_user.tenant_id} reset to sample data by user {current_user.id}")
        
        return ResetResponse(
            message="Data reset to sample state successfully",
            cleared=DataCounts(**result["cleared"]),
            seeded=DataCounts(**result["seeded"]),
        )
        
    except Exception as e:
        logger.error(f"Failed to reset data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset data: {str(e)}",
        )


@router.delete("/clear-all", response_model=DataCounts)
async def clear_all_data_endpoint(
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Clear all tenant data (except users).
    
    WARNING: This will delete ALL studies, packages, text elements, and
    related data. This action cannot be undone.
    
    Admin only.
    """
    try:
        counts = await clear_tenant_data(
            db,
            tenant_id=current_user.tenant_id,
            exclude_users=True,
        )
        
        logger.info(f"Tenant {current_user.tenant_id} data cleared by user {current_user.id}")
        
        return DataCounts(**counts)
        
    except Exception as e:
        logger.error(f"Failed to clear data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear data: {str(e)}",
        )


# =============================================================================
# Onboarding Endpoints
# =============================================================================

class OnboardingStatus(BaseModel):
    """Onboarding status for a tenant."""
    onboarding_completed: bool
    sample_data_seeded: bool
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
        sample_data_seeded=tenant.sample_data_seeded,
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
