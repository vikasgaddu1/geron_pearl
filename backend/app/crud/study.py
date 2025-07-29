"""CRUD operations for Study model."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study import Study
from app.schemas.study import StudyCreate, StudyUpdate


class StudyCRUD:
    """CRUD operations for Study model."""
    
    async def create(self, db: AsyncSession, *, obj_in: StudyCreate) -> Study:
        """Create a new study."""
        db_obj = Study(study_label=obj_in.study_label)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[Study]:
        """Get a study by ID."""
        result = await db.execute(select(Study).where(Study.id == id))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Study]:
        """Get multiple studies with pagination."""
        result = await db.execute(select(Study).offset(skip).limit(limit))
        return list(result.scalars().all())
    
    async def update(
        self, db: AsyncSession, *, db_obj: Study, obj_in: StudyUpdate
    ) -> Study:
        """Update an existing study."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[Study]:
        """Delete a study by ID."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
    
    async def get_by_label(self, db: AsyncSession, *, study_label: str) -> Optional[Study]:
        """Get a study by label."""
        result = await db.execute(select(Study).where(Study.study_label == study_label))
        return result.scalar_one_or_none()


# Create a global instance
study = StudyCRUD()