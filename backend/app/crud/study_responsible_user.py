"""CRUD operations for StudyResponsibleUser."""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import BaseCRUD
from app.models.study_responsible_user import StudyResponsibleUser
from app.models.user import User
from app.models.study import Study
from app.schemas.study_responsible_user import StudyResponsibleUserCreate, StudyResponsibleUserUpdate


class StudyResponsibleUserCRUD(BaseCRUD[StudyResponsibleUser, StudyResponsibleUserCreate, StudyResponsibleUserUpdate]):
    """CRUD operations for StudyResponsibleUser."""

    async def get_by_user_and_study(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        study_id: int
    ) -> Optional[StudyResponsibleUser]:
        """Get a user's responsible assignment for a specific study."""
        result = await db.execute(
            select(StudyResponsibleUser).where(
                and_(
                    StudyResponsibleUser.user_id == user_id,
                    StudyResponsibleUser.study_id == study_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: int
    ) -> List[StudyResponsibleUser]:
        """Get all studies where a user is responsible."""
        result = await db.execute(
            select(StudyResponsibleUser)
            .where(StudyResponsibleUser.user_id == user_id)
            .options(selectinload(StudyResponsibleUser.study))
        )
        return list(result.scalars().all())

    async def get_by_study(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> List[StudyResponsibleUser]:
        """Get all responsible users for a study."""
        result = await db.execute(
            select(StudyResponsibleUser)
            .where(StudyResponsibleUser.study_id == study_id)
            .options(selectinload(StudyResponsibleUser.user))
        )
        return list(result.scalars().all())

    async def is_responsible_for_study(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        study_id: int
    ) -> bool:
        """Check if a user is a responsible user for a specific study."""
        result = await self.get_by_user_and_study(db, user_id=user_id, study_id=study_id)
        return result is not None

    async def get_responsible_study_ids(
        self,
        db: AsyncSession,
        *,
        user_id: int
    ) -> List[int]:
        """Get list of study IDs where user is responsible."""
        result = await db.execute(
            select(StudyResponsibleUser.study_id)
            .where(StudyResponsibleUser.user_id == user_id)
        )
        return list(result.scalars().all())

    async def assign(
        self,
        db: AsyncSession,
        *,
        study_id: int,
        user_id: int,
        is_primary: bool = False
    ) -> StudyResponsibleUser:
        """
        Assign a user as responsible for a study.

        If is_primary is True and another user is already primary,
        this will make the new user primary (others remain non-primary).
        """
        # Check if assignment already exists
        existing = await self.get_by_user_and_study(db, user_id=user_id, study_id=study_id)
        if existing:
            # Update existing assignment
            existing.is_primary = is_primary
            if is_primary:
                # Clear other primary flags for this study
                await self._clear_other_primaries(db, study_id=study_id, exclude_user_id=user_id)
            await db.commit()
            await db.refresh(existing)
            return existing

        # If setting as primary, clear other primaries first
        if is_primary:
            await self._clear_other_primaries(db, study_id=study_id, exclude_user_id=user_id)

        # Create new assignment
        db_obj = StudyResponsibleUser(
            study_id=study_id,
            user_id=user_id,
            is_primary=is_primary
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(
        self,
        db: AsyncSession,
        *,
        study_id: int,
        user_id: int
    ) -> Optional[StudyResponsibleUser]:
        """
        Remove a user's responsible assignment from a study.

        Returns the removed assignment, or None if not found.
        """
        existing = await self.get_by_user_and_study(db, user_id=user_id, study_id=study_id)
        if existing:
            await db.delete(existing)
            await db.commit()
            return existing
        return None

    async def set_primary(
        self,
        db: AsyncSession,
        *,
        study_id: int,
        user_id: int,
        is_primary: bool
    ) -> Optional[StudyResponsibleUser]:
        """
        Update the primary status of a responsible user.

        If setting is_primary=True, clears primary from other users.
        """
        existing = await self.get_by_user_and_study(db, user_id=user_id, study_id=study_id)
        if not existing:
            return None

        if is_primary:
            await self._clear_other_primaries(db, study_id=study_id, exclude_user_id=user_id)

        existing.is_primary = is_primary
        await db.commit()
        await db.refresh(existing)
        return existing

    async def get_primary_responsible(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> Optional[User]:
        """Get the primary responsible user for a study."""
        result = await db.execute(
            select(User)
            .join(StudyResponsibleUser, User.id == StudyResponsibleUser.user_id)
            .where(
                and_(
                    StudyResponsibleUser.study_id == study_id,
                    StudyResponsibleUser.is_primary == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_responsible_users_with_details(
        self,
        db: AsyncSession,
        *,
        study_id: int
    ) -> List[dict]:
        """
        Get all responsible users for a study with user details.

        Returns list of dicts with user info and is_primary flag.
        """
        assignments = await self.get_by_study(db, study_id=study_id)

        result = []
        for assignment in assignments:
            user = assignment.user
            result.append({
                "id": assignment.id,
                "study_id": assignment.study_id,
                "user_id": user.id,
                "is_primary": assignment.is_primary,
                "username": user.username,
                "email": user.email,
                "created_at": assignment.created_at,
                "updated_at": assignment.updated_at
            })

        return result

    async def _clear_other_primaries(
        self,
        db: AsyncSession,
        *,
        study_id: int,
        exclude_user_id: int
    ) -> None:
        """Clear is_primary flag for all responsible users except the specified one."""
        result = await db.execute(
            select(StudyResponsibleUser).where(
                and_(
                    StudyResponsibleUser.study_id == study_id,
                    StudyResponsibleUser.user_id != exclude_user_id,
                    StudyResponsibleUser.is_primary == True
                )
            )
        )
        for assignment in result.scalars().all():
            assignment.is_primary = False


# Singleton instance
study_responsible_user = StudyResponsibleUserCRUD(StudyResponsibleUser)
