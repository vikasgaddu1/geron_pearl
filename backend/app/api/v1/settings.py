"""Application Settings API endpoints."""

from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import app_settings
from app.db.session import get_db
from app.schemas.app_settings import AppSettings, AppSettingsUpdate
from app.core.security import get_current_user, require_admin
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=AppSettings)
async def get_settings(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AppSettings:
    """
    Get application settings.

    Any authenticated user can view settings.
    """
    try:
        settings = await app_settings.get(db)

        # Build response with username if available
        return AppSettings(
            id=settings.id,
            default_due_date_offset=settings.default_due_date_offset,
            updated_by_user_id=settings.updated_by_user_id,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
            updated_by_username=settings.updated_by_user.username if settings.updated_by_user else None
        )
    except Exception as e:
        print(f"Error fetching settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve settings"
        )


@router.put("/", response_model=AppSettings)
async def update_settings(
    *,
    db: AsyncSession = Depends(get_db),
    settings_in: AppSettingsUpdate,
    current_user: User = Depends(require_admin()),
) -> AppSettings:
    """
    Update application settings (Admin only).

    Only administrators can modify settings.
    """
    try:
        settings = await app_settings.update(
            db,
            obj_in=settings_in,
            updated_by_user_id=current_user.id
        )

        print(f"Settings updated by user {current_user.username} (ID: {current_user.id})")

        # Build response with username
        return AppSettings(
            id=settings.id,
            default_due_date_offset=settings.default_due_date_offset,
            updated_by_user_id=settings.updated_by_user_id,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
            updated_by_username=settings.updated_by_user.username if settings.updated_by_user else None
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings"
        )


@router.get("/default-due-date-offset", response_model=Dict[str, int])
async def get_default_due_date_offset(
    *,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, int]:
    """
    Get just the default due date offset value.

    This endpoint is public and doesn't require authentication
    for easier integration with frontend forms.
    """
    try:
        offset = await app_settings.get_default_due_date_offset(db)
        return {"value": offset}
    except Exception as e:
        print(f"Error fetching due date offset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve setting"
        )
