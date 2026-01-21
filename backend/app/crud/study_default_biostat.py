"""CRUD operations for StudyDefaultBiostat."""

from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import BaseCRUD
from app.models.study_default_biostat import StudyDefaultBiostat
from app.schemas.study_default_biostat import StudyDefaultBiostatCreate, StudyDefaultBiostatUpdate


class StudyDefaultBiostatCRUD(BaseCRUD[StudyDefaultBiostat, StudyDefaultBiostatCreate, StudyDefaultBiostatUpdate]):
    """CRUD operations for StudyDefaultBiostat."""

    async def get_by_study(
        self,
        db: AsyncSession,
        *,
        study_id: int,
        active_only: bool = True
    ) -> Optional[StudyDefaultBiostat]:
        """Get the default biostat for a study."""
        query = select(StudyDefaultBiostat).where(StudyDefaultBiostat.study_id == study_id)
        if active_only:
            query = query.where(StudyDefaultBiostat.is_active == True)  # noqa: E712
        query = query.options(selectinload(StudyDefaultBiostat.user))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_study_with_user(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> Optional[StudyDefaultBiostat]:
        """Get the active default biostat for a study with user details."""
        result = await db.execute(
            select(StudyDefaultBiostat)
            .where(
                and_(
                    StudyDefaultBiostat.study_id == study_id,
                    StudyDefaultBiostat.is_active == True  # noqa: E712
                )
            )
            .options(selectinload(StudyDefaultBiostat.user))
        )
        return result.scalar_one_or_none()

    async def get_active_biostat_user_id(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> Optional[int]:
        """Get just the user_id of the active default biostat for a study."""
        result = await db.execute(
            select(StudyDefaultBiostat.user_id)
            .where(
                and_(
                    StudyDefaultBiostat.study_id == study_id,
                    StudyDefaultBiostat.is_active == True  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def set_default_biostat(
        self,
        db: AsyncSession,
        *,
        study_id: int,
        user_id: int
    ) -> StudyDefaultBiostat:
        """
        Set the default biostat for a study.

        If a default biostat already exists, deactivate it and create a new one.
        """
        # Deactivate any existing default biostat
        existing = await self.get_by_study(db, study_id=study_id, active_only=True)
        if existing:
            existing.is_active = False
            db.add(existing)

        # Check if this user was previously a default biostat for this study
        result = await db.execute(
            select(StudyDefaultBiostat).where(
                and_(
                    StudyDefaultBiostat.study_id == study_id,
                    StudyDefaultBiostat.user_id == user_id
                )
            )
        )
        reuse_record = result.scalar_one_or_none()

        if reuse_record:
            # Reactivate existing record
            reuse_record.is_active = True
            db.add(reuse_record)
            await db.flush()
            await db.refresh(reuse_record)
            return reuse_record
        else:
            # Create new record
            new_default = StudyDefaultBiostat(
                study_id=study_id,
                user_id=user_id,
                is_active=True
            )
            db.add(new_default)
            await db.flush()
            await db.refresh(new_default)
            return new_default

    async def remove_default_biostat(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> bool:
        """
        Remove the default biostat for a study (deactivate).

        Returns True if a default was found and deactivated.
        """
        existing = await self.get_by_study(db, study_id=study_id, active_only=True)
        if existing:
            existing.is_active = False
            db.add(existing)
            await db.flush()
            return True
        return False


# Create singleton instance
study_default_biostat = StudyDefaultBiostatCRUD(StudyDefaultBiostat)
