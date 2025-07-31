"""CRUD operations for AcronymSetMember model."""

from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.acronym_set_member import AcronymSetMember
from app.schemas.acronym_set_member import AcronymSetMemberCreate, AcronymSetMemberUpdate


class AcronymSetMemberCRUD:
    """CRUD operations for AcronymSetMember model."""
    
    async def create(self, db: AsyncSession, *, obj_in: AcronymSetMemberCreate) -> AcronymSetMember:
        """Create a new acronym set member."""
        db_obj = AcronymSetMember(
            acronym_set_id=obj_in.acronym_set_id,
            acronym_id=obj_in.acronym_id,
            sort_order=obj_in.sort_order
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[AcronymSetMember]:
        """Get an acronym set member by ID."""
        result = await db.execute(select(AcronymSetMember).where(AcronymSetMember.id == id))
        return result.scalar_one_or_none()
    
    async def get_with_relations(self, db: AsyncSession, *, id: int) -> Optional[AcronymSetMember]:
        """Get an acronym set member by ID with acronym and set loaded."""
        result = await db.execute(
            select(AcronymSetMember)
            .options(
                selectinload(AcronymSetMember.acronym),
                selectinload(AcronymSetMember.acronym_set)
            )
            .where(AcronymSetMember.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[AcronymSetMember]:
        """Get multiple acronym set members with pagination."""
        result = await db.execute(select(AcronymSetMember).offset(skip).limit(limit))
        return list(result.scalars().all())
    
    async def get_by_set_id(
        self, db: AsyncSession, *, acronym_set_id: int
    ) -> List[AcronymSetMember]:
        """Get all members of a specific acronym set (no pagination)."""
        result = await db.execute(
            select(AcronymSetMember)
            .options(selectinload(AcronymSetMember.acronym))
            .where(AcronymSetMember.acronym_set_id == acronym_set_id)
            .order_by(AcronymSetMember.sort_order, AcronymSetMember.id)
        )
        return list(result.scalars().all())
    
    async def get_by_acronym_id(
        self, db: AsyncSession, *, acronym_id: int
    ) -> List[AcronymSetMember]:
        """Get all set memberships for a specific acronym."""
        result = await db.execute(
            select(AcronymSetMember)
            .options(selectinload(AcronymSetMember.acronym_set))
            .where(AcronymSetMember.acronym_id == acronym_id)
        )
        return list(result.scalars().all())
    
    async def get_by_set_and_acronym(
        self, db: AsyncSession, *, acronym_set_id: int, acronym_id: int
    ) -> Optional[AcronymSetMember]:
        """Get a specific acronym set member by set and acronym IDs."""
        result = await db.execute(
            select(AcronymSetMember)
            .where(
                and_(
                    AcronymSetMember.acronym_set_id == acronym_set_id,
                    AcronymSetMember.acronym_id == acronym_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def update(
        self, db: AsyncSession, *, db_obj: AcronymSetMember, obj_in: AcronymSetMemberUpdate
    ) -> AcronymSetMember:
        """Update an existing acronym set member."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[AcronymSetMember]:
        """Delete an acronym set member by ID."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
    
    async def remove_from_set(
        self, db: AsyncSession, *, acronym_set_id: int, acronym_id: int
    ) -> Optional[AcronymSetMember]:
        """Remove an acronym from a specific set."""
        db_obj = await self.get_by_set_and_acronym(
            db, acronym_set_id=acronym_set_id, acronym_id=acronym_id
        )
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj


# Create a global instance
acronym_set_member = AcronymSetMemberCRUD()