"""CRUD operations for Package model."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.package import Package
from app.schemas.package import PackageCreate, PackageUpdate


class PackageCRUD:
    """CRUD operations for Package model."""
    
    async def create(self, db: AsyncSession, *, obj_in: PackageCreate) -> Package:
        """Create a new package."""
        db_obj = Package(package_name=obj_in.package_name)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[Package]:
        """Get a package by ID."""
        result = await db.execute(select(Package).where(Package.id == id))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Package]:
        """Get multiple packages with pagination."""
        result = await db.execute(select(Package).offset(skip).limit(limit))
        return list(result.scalars().all())
    
    async def update(
        self, db: AsyncSession, *, db_obj: Package, obj_in: PackageUpdate
    ) -> Package:
        """Update an existing package."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[Package]:
        """Delete a package by ID."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
    
    async def get_by_name(self, db: AsyncSession, *, package_name: str) -> Optional[Package]:
        """Get a package by name."""
        result = await db.execute(select(Package).where(Package.package_name == package_name))
        return result.scalar_one_or_none()


# Create a global instance
package = PackageCRUD()