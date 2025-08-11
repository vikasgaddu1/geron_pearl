"""CRUD operations for ReportingEffort model."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reporting_effort import ReportingEffort
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
        """Get a reporting effort by ID."""
        result = await db.execute(select(ReportingEffort).where(ReportingEffort.id == id))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ReportingEffort]:
        """Get multiple reporting efforts with pagination."""
        result = await db.execute(select(ReportingEffort).offset(skip).limit(limit))
        return list(result.scalars().all())
    
    async def get_by_study(
        self, db: AsyncSession, *, study_id: int, skip: int = 0, limit: int = 100
    ) -> List[ReportingEffort]:
        """Get reporting efforts for a specific study with pagination."""
        result = await db.execute(
            select(ReportingEffort)
            .where(ReportingEffort.study_id == study_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_study_id(self, db: AsyncSession, *, study_id: int) -> List[ReportingEffort]:
        """Get all reporting efforts for a specific study (no pagination)."""
        result = await db.execute(
            select(ReportingEffort).where(ReportingEffort.study_id == study_id)
        )
        return list(result.scalars().all())
    
    async def get_by_database_release(
        self, db: AsyncSession, *, database_release_id: int, skip: int = 0, limit: int = 100
    ) -> List[ReportingEffort]:
        """Get reporting efforts for a specific database release with pagination."""
        result = await db.execute(
            select(ReportingEffort)
            .where(ReportingEffort.database_release_id == database_release_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_database_release_id(self, db: AsyncSession, *, database_release_id: int) -> List[ReportingEffort]:
        """Get all reporting efforts for a specific database release (no pagination)."""
        result = await db.execute(
            select(ReportingEffort).where(ReportingEffort.database_release_id == database_release_id)
        )
        return list(result.scalars().all())
    
    async def get_by_study_and_database_release(
        self, db: AsyncSession, *, study_id: int, database_release_id: int
    ) -> List[ReportingEffort]:
        """Get reporting efforts for a specific study and database release combination."""
        result = await db.execute(
            select(ReportingEffort).where(
                ReportingEffort.study_id == study_id,
                ReportingEffort.database_release_id == database_release_id
            )
        )
        return list(result.scalars().all())
    
    async def get_by_release_and_label(
        self, db: AsyncSession, *, database_release_id: int, database_release_label: str
    ) -> Optional[ReportingEffort]:
        """Get a reporting effort by database release ID and label (case and space insensitive)."""
        # Normalize the input label: remove spaces and convert to uppercase
        normalized_input = database_release_label.replace(" ", "").upper()
        
        # Get all efforts for this release and check normalized labels
        result = await db.execute(
            select(ReportingEffort).where(ReportingEffort.database_release_id == database_release_id)
        )
        efforts = result.scalars().all()
        
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


# Create a global instance
reporting_effort = ReportingEffortCRUD()