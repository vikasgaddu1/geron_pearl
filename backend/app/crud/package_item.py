"""CRUD operations for PackageItem model and related details."""

from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.package_item import PackageItem
from app.models.package_tlf_details import PackageTlfDetails
from app.models.package_dataset_details import PackageDatasetDetails
from app.models.package_item_footnote import PackageItemFootnote
from app.models.package_item_acronym import PackageItemAcronym
from app.schemas.package_item import (
    PackageItemCreate, PackageItemUpdate, PackageItemCreateWithDetails,
    ItemTypeEnum
)


class PackageItemCRUD:
    """CRUD operations for PackageItem model."""
    
    async def create(self, db: AsyncSession, *, obj_in: PackageItemCreate) -> PackageItem:
        """Create a new package item."""
        db_obj = PackageItem(
            package_id=obj_in.package_id,
            study_id=obj_in.study_id,
            item_type=obj_in.item_type,
            item_subtype=obj_in.item_subtype,
            item_code=obj_in.item_code
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def create_with_details(
        self, db: AsyncSession, *, obj_in: PackageItemCreateWithDetails
    ) -> PackageItem:
        """Create a package item with all details and associations."""
        # Create the main package item
        db_obj = PackageItem(
            package_id=obj_in.package_id,
            study_id=obj_in.study_id,
            item_type=obj_in.item_type,
            item_subtype=obj_in.item_subtype,
            item_code=obj_in.item_code
        )
        db.add(db_obj)
        await db.flush()  # Get the ID without committing
        
        # Create TLF details if provided and item is TLF
        if obj_in.item_type == ItemTypeEnum.TLF and obj_in.tlf_details:
            tlf_details = PackageTlfDetails(
                package_item_id=db_obj.id,
                title_id=obj_in.tlf_details.title_id,
                population_flag_id=obj_in.tlf_details.population_flag_id
            )
            db.add(tlf_details)
        
        # Create Dataset details if provided and item is Dataset
        elif obj_in.item_type == ItemTypeEnum.Dataset and obj_in.dataset_details:
            dataset_details = PackageDatasetDetails(
                package_item_id=db_obj.id,
                label=obj_in.dataset_details.label,
                sorting_order=obj_in.dataset_details.sorting_order,
                acronyms=obj_in.dataset_details.acronyms
            )
            db.add(dataset_details)
        
        # Create footnote associations
        for footnote in obj_in.footnotes:
            footnote_assoc = PackageItemFootnote(
                package_item_id=db_obj.id,
                footnote_id=footnote.footnote_id,
                sequence_number=footnote.sequence_number
            )
            db.add(footnote_assoc)
        
        # Create acronym associations
        for acronym in obj_in.acronyms:
            acronym_assoc = PackageItemAcronym(
                package_item_id=db_obj.id,
                acronym_id=acronym.acronym_id
            )
            db.add(acronym_assoc)
        
        await db.commit()
        await db.refresh(db_obj)
        
        # Load all relationships
        result = await db.execute(
            select(PackageItem)
            .options(
                selectinload(PackageItem.tlf_details),
                selectinload(PackageItem.dataset_details),
                selectinload(PackageItem.footnotes),
                selectinload(PackageItem.acronyms)
            )
            .where(PackageItem.id == db_obj.id)
        )
        return result.scalar_one()
    
    async def get(self, db: AsyncSession, *, id: int) -> Optional[PackageItem]:
        """Get a package item by ID with all relationships."""
        result = await db.execute(
            select(PackageItem)
            .options(
                selectinload(PackageItem.tlf_details),
                selectinload(PackageItem.dataset_details),
                selectinload(PackageItem.footnotes),
                selectinload(PackageItem.acronyms),
                selectinload(PackageItem.study)
            )
            .where(PackageItem.id == id)
        )
        item = result.scalar_one_or_none()
        if item and item.study:
            item.study_label = item.study.study_label
        return item
    
    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[PackageItem]:
        """Get multiple package items with pagination."""
        result = await db.execute(
            select(PackageItem)
            .options(
                selectinload(PackageItem.tlf_details),
                selectinload(PackageItem.dataset_details),
                selectinload(PackageItem.footnotes),
                selectinload(PackageItem.acronyms)
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_package_id(
        self, db: AsyncSession, *, package_id: int
    ) -> List[PackageItem]:
        """Get all package items for a specific package (no pagination)."""
        result = await db.execute(
            select(PackageItem)
            .options(
                selectinload(PackageItem.tlf_details),
                selectinload(PackageItem.dataset_details),
                selectinload(PackageItem.footnotes),
                selectinload(PackageItem.acronyms),
                selectinload(PackageItem.study)
            )
            .where(PackageItem.package_id == package_id)
        )
        items = list(result.scalars().all())
        # Add study_label to each item for convenience
        for item in items:
            if item.study:
                item.study_label = item.study.study_label
        return items
    
    async def get_by_study_id(
        self, db: AsyncSession, *, study_id: int
    ) -> List[PackageItem]:
        """Get all package items for a specific study (no pagination)."""
        result = await db.execute(
            select(PackageItem)
            .options(
                selectinload(PackageItem.tlf_details),
                selectinload(PackageItem.dataset_details),
                selectinload(PackageItem.footnotes),
                selectinload(PackageItem.acronyms)
            )
            .where(PackageItem.study_id == study_id)
        )
        return list(result.scalars().all())
    
    async def get_by_unique_key(
        self, db: AsyncSession, *, 
        package_id: int, 
        item_type: str,
        item_subtype: str,
        item_code: str
    ) -> Optional[PackageItem]:
        """Get a package item by its unique key combination."""
        result = await db.execute(
            select(PackageItem).where(
                and_(
                    PackageItem.package_id == package_id,
                    PackageItem.item_type == item_type,
                    PackageItem.item_subtype == item_subtype,
                    PackageItem.item_code == item_code
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def update(
        self, db: AsyncSession, *, db_obj: PackageItem, obj_in: PackageItemUpdate
    ) -> PackageItem:
        """Update an existing package item."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Reload with relationships
        result = await db.execute(
            select(PackageItem)
            .options(
                selectinload(PackageItem.tlf_details),
                selectinload(PackageItem.dataset_details),
                selectinload(PackageItem.footnotes),
                selectinload(PackageItem.acronyms)
            )
            .where(PackageItem.id == db_obj.id)
        )
        return result.scalar_one()
    
    async def delete(self, db: AsyncSession, *, id: int) -> Optional[PackageItem]:
        """Delete a package item by ID."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            # Delete related details first (if any)
            if db_obj.tlf_details:
                await db.delete(db_obj.tlf_details)
            if db_obj.dataset_details:
                await db.delete(db_obj.dataset_details)
            
            # Delete footnote associations
            for footnote in db_obj.footnotes:
                await db.delete(footnote)
            
            # Delete acronym associations
            for acronym in db_obj.acronyms:
                await db.delete(acronym)
            
            # Delete the package item itself
            await db.delete(db_obj)
            await db.commit()
        return db_obj


# Create a global instance
package_item = PackageItemCRUD()