"""CRUD operations for AcronymSet model."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.acronym_set import AcronymSet
from app.schemas.acronym_set import AcronymSetCreate, AcronymSetUpdate


class AcronymSetCRUD:
    """CRUD operations for AcronymSet model."""
    
    async def create(self, db: AsyncSession, *, obj_in: AcronymSetCreate) -> AcronymSet:
        """Create a new acronym set."""
        db_obj = AcronymSet(
            name=obj_in.name,
            description=obj_in.description
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[AcronymSet]:
        """Get an acronym set by ID."""
        result = await db.execute(select(AcronymSet).where(AcronymSet.id == id))
        return result.scalar_one_or_none()
    
    async def get_with_members(self, db: AsyncSession, *, id: int) -> Optional[AcronymSet]:
        """Get an acronym set by ID with its members loaded."""
        result = await db.execute(
            select(AcronymSet)
            .options(
                selectinload(AcronymSet.acronym_set_members)
                .selectinload(AcronymSet.acronym_set_members.property.entity.acronym)
            )
            .where(AcronymSet.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[AcronymSet]:
        """Get multiple acronym sets with pagination."""
        result = await db.execute(select(AcronymSet).offset(skip).limit(limit))
        return list(result.scalars().all())
    
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[AcronymSet]:
        """Get an acronym set by name."""
        result = await db.execute(select(AcronymSet).where(AcronymSet.name == name))
        return result.scalar_one_or_none()
    
    async def update(
        self, db: AsyncSession, *, db_obj: AcronymSet, obj_in: AcronymSetUpdate
    ) -> AcronymSet:
        """Update an existing acronym set."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[AcronymSet]:
        """Delete an acronym set by ID."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
    
    async def search_by_name(
        self, db: AsyncSession, *, search_term: str, skip: int = 0, limit: int = 100
    ) -> List[AcronymSet]:
        """Search acronym sets by name or description."""
        result = await db.execute(
            select(AcronymSet)
            .where(
                AcronymSet.name.ilike(f"%{search_term}%") |
                AcronymSet.description.ilike(f"%{search_term}%")
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


# Create a global instance
acronym_set = AcronymSetCRUD()