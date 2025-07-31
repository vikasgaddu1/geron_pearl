"""CRUD operations for Acronym model."""

from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acronym import Acronym
from app.schemas.acronym import AcronymCreate, AcronymUpdate


class AcronymCRUD:
    """CRUD operations for Acronym model."""
    
    async def create(self, db: AsyncSession, *, obj_in: AcronymCreate) -> Acronym:
        """Create a new acronym."""
        db_obj = Acronym(
            key=obj_in.key,
            value=obj_in.value,
            description=obj_in.description
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[Acronym]:
        """Get an acronym by ID."""
        result = await db.execute(select(Acronym).where(Acronym.id == id))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Acronym]:
        """Get multiple acronyms with pagination."""
        result = await db.execute(select(Acronym).offset(skip).limit(limit))
        return list(result.scalars().all())
    
    async def get_by_key(self, db: AsyncSession, *, key: str) -> Optional[Acronym]:
        """Get an acronym by key."""
        result = await db.execute(select(Acronym).where(Acronym.key == key))
        return result.scalar_one_or_none()
    
    async def update(
        self, db: AsyncSession, *, db_obj: Acronym, obj_in: AcronymUpdate
    ) -> Acronym:
        """Update an existing acronym."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[Acronym]:
        """Delete an acronym by ID."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
    
    async def search(
        self, db: AsyncSession, *, search_term: str, skip: int = 0, limit: int = 100
    ) -> List[Acronym]:
        """Search acronyms by key, value, or description."""
        result = await db.execute(
            select(Acronym)
            .where(
                or_(
                    Acronym.key.ilike(f"%{search_term}%"),
                    Acronym.value.ilike(f"%{search_term}%"),
                    Acronym.description.ilike(f"%{search_term}%")
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


# Create a global instance
acronym = AcronymCRUD()