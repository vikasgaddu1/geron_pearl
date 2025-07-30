"""CRUD operations for DatabaseRelease model."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database_release import DatabaseRelease
from app.schemas.database_release import DatabaseReleaseCreate, DatabaseReleaseUpdate


class DatabaseReleaseCRUD:
    """CRUD operations for DatabaseRelease model."""
    
    async def create(self, db: AsyncSession, *, obj_in: DatabaseReleaseCreate) -> DatabaseRelease:
        """Create a new database release."""
        db_obj = DatabaseRelease(
            study_id=obj_in.study_id,
            database_release_label=obj_in.database_release_label
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[DatabaseRelease]:
        """Get a database release by ID."""
        result = await db.execute(select(DatabaseRelease).where(DatabaseRelease.id == id))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[DatabaseRelease]:
        """Get multiple database releases with pagination."""
        result = await db.execute(select(DatabaseRelease).offset(skip).limit(limit))
        return list(result.scalars().all())
    
    async def get_by_study(
        self, db: AsyncSession, *, study_id: int, skip: int = 0, limit: int = 100
    ) -> List[DatabaseRelease]:
        """Get database releases for a specific study with pagination."""
        result = await db.execute(
            select(DatabaseRelease)
            .where(DatabaseRelease.study_id == study_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_study_id(self, db: AsyncSession, *, study_id: int) -> List[DatabaseRelease]:
        """Get all database releases for a specific study (no pagination)."""
        result = await db.execute(
            select(DatabaseRelease).where(DatabaseRelease.study_id == study_id)
        )
        return list(result.scalars().all())
    
    async def get_by_study_and_label(
        self, db: AsyncSession, *, study_id: int, database_release_label: str
    ) -> Optional[DatabaseRelease]:
        """Get a database release by study ID and label."""
        result = await db.execute(
            select(DatabaseRelease).where(
                DatabaseRelease.study_id == study_id,
                DatabaseRelease.database_release_label == database_release_label
            )
        )
        return result.scalar_one_or_none()
    
    async def update(
        self, db: AsyncSession, *, db_obj: DatabaseRelease, obj_in: DatabaseReleaseUpdate
    ) -> DatabaseRelease:
        """Update an existing database release."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[DatabaseRelease]:
        """Delete a database release by ID."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj


# Create a global instance
database_release = DatabaseReleaseCRUD()