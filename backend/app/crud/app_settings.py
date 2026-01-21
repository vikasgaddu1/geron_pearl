"""CRUD operations for AppSettings model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.app_settings import AppSettings
from app.schemas.app_settings import AppSettingsUpdate


class AppSettingsCRUD:
    """CRUD operations for AppSettings model.

    This is a singleton table - there's only ever one row with id=1.
    The get() method creates the default row if it doesn't exist.
    """

    async def get(self, db: AsyncSession, *, tenant_id: int = None) -> AppSettings:
        """Get application settings for a tenant.

        If no settings exist for the tenant, creates the default settings row.
        Always returns a settings object.

        Args:
            db: Database session
            tenant_id: Tenant ID (defaults to 1 if not provided)
        """
        # Use provided tenant_id or default to 1
        settings_tenant_id = tenant_id if tenant_id is not None else 1

        result = await db.execute(
            select(AppSettings)
            .options(joinedload(AppSettings.updated_by_user))
            .where(AppSettings.tenant_id == settings_tenant_id)
        )
        settings = result.scalar_one_or_none()

        if settings is None:
            # Create default settings for this tenant
            settings = AppSettings(
                tenant_id=settings_tenant_id,
                default_due_date_offset=7
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)

        return settings

    async def update(
        self,
        db: AsyncSession,
        *,
        obj_in: AppSettingsUpdate,
        updated_by_user_id: Optional[int] = None,
        tenant_id: int = None
    ) -> AppSettings:
        """Update application settings.

        Args:
            db: Database session
            obj_in: Update schema with new values
            updated_by_user_id: ID of user making the update
            tenant_id: Tenant ID (defaults to 1 if not provided)

        Returns:
            Updated settings object
        """
        # Get current settings (creates if not exists)
        settings = await self.get(db, tenant_id=tenant_id)

        # Apply updates
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(settings, field, value)

        # Track who updated and when
        settings.updated_by_user_id = updated_by_user_id
        settings.updated_at = datetime.utcnow()

        db.add(settings)
        await db.commit()

        # Refresh with user relationship loaded
        settings_tenant_id = tenant_id if tenant_id is not None else 1
        result = await db.execute(
            select(AppSettings)
            .options(joinedload(AppSettings.updated_by_user))
            .where(AppSettings.tenant_id == settings_tenant_id)
        )
        return result.scalar_one()

    async def get_default_due_date_offset(self, db: AsyncSession, *, tenant_id: int = None) -> int:
        """Convenience method to get just the due date offset value.

        Args:
            db: Database session
            tenant_id: Tenant ID (defaults to 1 if not provided)

        Returns:
            Default due date offset in days (default 7)
        """
        settings = await self.get(db, tenant_id=tenant_id)
        return settings.default_due_date_offset


# Create a global instance
app_settings = AppSettingsCRUD()
