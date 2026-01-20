"""Tenant data management endpoints.

This module provides endpoints for:
- Resetting tenant data to sample state
- Checking sample data status
- Seeding sample data on demand
- Marking onboarding as complete
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
