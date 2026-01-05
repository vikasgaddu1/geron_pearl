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

    async def get(self, db: AsyncSession) -> AppSettings:
        """Get application settings.

        If no settings exist, creates the default settings row.
        Always returns a settings object.
        """
        result = await db.execute(
            select(AppSettings)
            .options(joinedload(AppSettings.updated_by_user))
            .where(AppSettings.id == 1)
        )
        settings = result.scalar_one_or_none()

        if settings is None:
            # Create default settings
            settings = AppSettings(
                id=1,
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
        updated_by_user_id: Optional[int] = None
    ) -> AppSettings:
        """Update application settings.

        Args:
            db: Database session
            obj_in: Update schema with new values
            updated_by_user_id: ID of user making the update

        Returns:
            Updated settings object
        """
        # Get current settings (creates if not exists)
        settings = await self.get(db)

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
        result = await db.execute(
            select(AppSettings)
            .options(joinedload(AppSettings.updated_by_user))
            .where(AppSettings.id == 1)
        )
        return result.scalar_one()

    async def get_default_due_date_offset(self, db: AsyncSession) -> int:
        """Convenience method to get just the due date offset value.

        Returns:
            Default due date offset in days (default 7)
        """
        settings = await self.get(db)
        return settings.default_due_date_offset


# Create a global instance
app_settings = AppSettingsCRUD()
