"""CRUD operations for ReportingEffort model."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.reporting_effort import ReportingEffort
from app.models.reporting_effort_item import ReportingEffortItem
from app.models.reporting_effort_lock_history import ReportingEffortLockHistory
from app.models.enums import LockAction
from app.schemas.reporting_effort import ReportingEffortCreate, ReportingEffortUpdate


class ReportingEffortCRUD:
    """CRUD operations for ReportingEffort model."""
    
    async def create(self, db: AsyncSession, *, obj_in: ReportingEffortCreate) -> ReportingEffort:
        """Create a new reporting effort."""
        db_obj = ReportingEffort(
            study_id=obj_in.study_id,
            database_release_id=obj_in.database_release_id,
            database_release_label=obj_in.database_release_label
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[ReportingEffort]:
        """Get a reporting effort by ID with related data."""
        result = await db.execute(
            select(ReportingEffort)
            .options(
                joinedload(ReportingEffort.study),
                joinedload(ReportingEffort.database_release),
                joinedload(ReportingEffort.locked_by)
            )
            .where(ReportingEffort.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ReportingEffort]:
        """Get multiple reporting efforts with pagination and related data."""
        result = await db.execute(
            select(ReportingEffort)
            .options(
                joinedload(ReportingEffort.study),
                joinedload(ReportingEffort.database_release),
                joinedload(ReportingEffort.locked_by)
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.unique().scalars().all())
    
    async def get_by_study(
        self, db: AsyncSession, *, study_id: int, skip: int = 0, limit: int = 100
    ) -> List[ReportingEffort]:
        """Get reporting efforts for a specific study with pagination and related data."""
        result = await db.execute(
            select(ReportingEffort)
            .options(
                joinedload(ReportingEffort.study),
                joinedload(ReportingEffort.database_release),
                joinedload(ReportingEffort.locked_by)
            )
            .where(ReportingEffort.study_id == study_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.unique().scalars().all())

    async def get_by_database_release(
        self, db: AsyncSession, *, database_release_id: int, skip: int = 0, limit: int = 100
    ) -> List[ReportingEffort]:
        """Get reporting efforts for a specific database release with pagination and related data."""
        result = await db.execute(
            select(ReportingEffort)
            .options(
                joinedload(ReportingEffort.study),
                joinedload(ReportingEffort.database_release),
                joinedload(ReportingEffort.locked_by)
            )
            .where(ReportingEffort.database_release_id == database_release_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.unique().scalars().all())
    
    async def get_by_database_release_id(self, db: AsyncSession, *, database_release_id: int) -> List[ReportingEffort]:
        """Get all reporting efforts for a specific database release (no pagination) with related data."""
        result = await db.execute(
            select(ReportingEffort)
            .options(
                joinedload(ReportingEffort.study),
                joinedload(ReportingEffort.database_release),
                joinedload(ReportingEffort.locked_by)
            )
            .where(ReportingEffort.database_release_id == database_release_id)
        )
        return list(result.unique().scalars().all())
    
    async def get_by_study_and_database_release(
        self, db: AsyncSession, *, study_id: int, database_release_id: int
    ) -> List[ReportingEffort]:
        """Get reporting efforts for a specific study and database release combination with related data."""
        result = await db.execute(
            select(ReportingEffort)
            .options(
                joinedload(ReportingEffort.study),
                joinedload(ReportingEffort.database_release),
                joinedload(ReportingEffort.locked_by)
            )
            .where(
                ReportingEffort.study_id == study_id,
                ReportingEffort.database_release_id == database_release_id
            )
        )
        return list(result.unique().scalars().all())
    
    async def get_by_release_and_label(
        self, db: AsyncSession, *, database_release_id: int, database_release_label: str
    ) -> Optional[ReportingEffort]:
        """Get a reporting effort by database release ID and label (case and space insensitive) with related data."""
        # Normalize the input label: remove spaces and convert to uppercase
        normalized_input = database_release_label.replace(" ", "").upper()
        
        # Get all efforts for this release and check normalized labels
        result = await db.execute(
            select(ReportingEffort)
            .options(
                joinedload(ReportingEffort.study),
                joinedload(ReportingEffort.database_release),
                joinedload(ReportingEffort.locked_by)
            )
            .where(ReportingEffort.database_release_id == database_release_id)
        )
        efforts = result.unique().scalars().all()
        
        for effort in efforts:
            # Normalize each stored label and compare
            normalized_stored = effort.database_release_label.replace(" ", "").upper()
            if normalized_stored == normalized_input:
                return effort
        
        return None
    
    async def update(
        self, db: AsyncSession, *, db_obj: ReportingEffort, obj_in: ReportingEffortUpdate
    ) -> ReportingEffort:
        """Update an existing reporting effort."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[ReportingEffort]:
        """Delete a reporting effort by ID."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj

    async def get_items_count(self, db: AsyncSession, *, id: int) -> int:
        """Get count of reporting effort items for a reporting effort."""
        result = await db.execute(
            select(func.count(ReportingEffortItem.id))
            .where(ReportingEffortItem.reporting_effort_id == id)
        )
        return result.scalar() or 0

    # ==================== Lock/Unlock Operations ====================

    async def lock(
        self, db: AsyncSession, *, id: int, user_id: int, reason: str
    ) -> ReportingEffort:
        """Lock a reporting effort with a reason."""
        db_obj = await self.get(db, id=id)
        if not db_obj:
            raise ValueError(f"Reporting effort with id {id} not found")

        if db_obj.is_locked:
            raise ValueError("Reporting effort is already locked")

        # Update the reporting effort
        db_obj.is_locked = True
        db_obj.locked_at = datetime.utcnow()
        db_obj.locked_by_id = user_id
        db_obj.lock_reason = reason

        # Create history entry
        history_entry = ReportingEffortLockHistory(
            reporting_effort_id=id,
            performed_by_id=user_id,
            action=LockAction.LOCK,
            reason=reason
        )
        db.add(history_entry)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def unlock(
        self, db: AsyncSession, *, id: int, user_id: int, reason: str
    ) -> ReportingEffort:
        """Unlock a reporting effort with a reason."""
        db_obj = await self.get(db, id=id)
        if not db_obj:
            raise ValueError(f"Reporting effort with id {id} not found")

        if not db_obj.is_locked:
            raise ValueError("Reporting effort is not locked")

        # Update the reporting effort - clear lock metadata since it's no longer locked
        # The unlock details are preserved in the history table
        db_obj.is_locked = False
        db_obj.locked_at = None
        db_obj.locked_by_id = None
        db_obj.lock_reason = None

        # Create history entry (this preserves the unlock details)
        history_entry = ReportingEffortLockHistory(
            reporting_effort_id=id,
            performed_by_id=user_id,
            action=LockAction.UNLOCK,
            reason=reason
        )
        db.add(history_entry)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_lock_history(
        self, db: AsyncSession, *, id: int
    ) -> List[ReportingEffortLockHistory]:
        """Get the lock/unlock history for a reporting effort."""
        result = await db.execute(
            select(ReportingEffortLockHistory)
            .options(joinedload(ReportingEffortLockHistory.performed_by))
            .where(ReportingEffortLockHistory.reporting_effort_id == id)
            .order_by(ReportingEffortLockHistory.created_at.desc())
        )
        return list(result.unique().scalars().all())

    async def is_locked(self, db: AsyncSession, *, id: int) -> bool:
        """Quick check if a reporting effort is locked."""
        result = await db.execute(
            select(ReportingEffort.is_locked)
            .where(ReportingEffort.id == id)
        )
        is_locked = result.scalar_one_or_none()
        return is_locked if is_locked is not None else False

    async def check_lock_and_get_reason(
        self, db: AsyncSession, *, id: int
    ) -> tuple[bool, Optional[str]]:
        """Check if locked and return the lock reason if so."""
        result = await db.execute(
            select(ReportingEffort.is_locked, ReportingEffort.lock_reason)
            .where(ReportingEffort.id == id)
        )
        row = result.one_or_none()
        if row is None:
            return False, None
        return row[0], row[1] if row[0] else None


# Create a global instance
reporting_effort = ReportingEffortCRUD()