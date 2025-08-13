"""CRUD operations for ReportingEffortItem."""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reporting_effort_item import ReportingEffortItem
from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
from app.models.reporting_effort_tlf_details import ReportingEffortTlfDetails
from app.models.reporting_effort_dataset_details import ReportingEffortDatasetDetails
from app.models.reporting_effort_item_footnote import ReportingEffortItemFootnote
from app.models.reporting_effort_item_acronym import ReportingEffortItemAcronym
from app.models.package_item import ItemType
from app.schemas.reporting_effort_item import (
    ReportingEffortItemCreate,
    ReportingEffortItemUpdate
)


class ReportingEffortItemCRUD:
    """CRUD operations for ReportingEffortItem."""
    
    async def create_with_details(
        self,
        db: AsyncSession,
        *,
        obj_in: ReportingEffortItemCreate,
        tlf_details: Optional[Dict[str, Any]] = None,
        dataset_details: Optional[Dict[str, Any]] = None,
        footnote_ids: Optional[List[int]] = None,
        acronym_ids: Optional[List[int]] = None,
        auto_create_tracker: bool = True
    ) -> ReportingEffortItem:
        """
        Create a reporting effort item with all related details.
        
        Args:
            db: Database session
            obj_in: Item creation data
            tlf_details: TLF-specific details (if item_type is TLF)
            dataset_details: Dataset-specific details (if item_type is Dataset)
            footnote_ids: List of footnote IDs to associate
            acronym_ids: List of acronym IDs to associate
            auto_create_tracker: Whether to auto-create tracker entry
        
        Returns:
            Created item with all relationships
        """
        # Create main item (use mode='json' to properly serialize enums)
        item_data = obj_in.model_dump(mode='json')
        # Normalize enum to lowercase values to match DB enum labels
        source_type_value = item_data.get("source_type")
        if source_type_value is not None:
            if isinstance(source_type_value, str):
                item_data["source_type"] = source_type_value.lower()
            else:
                try:
                    item_data["source_type"] = source_type_value.value
                except AttributeError:
                    item_data["source_type"] = str(source_type_value).lower()
        print(f"DEBUG: Creating ReportingEffortItem with data: {item_data}")
        db_obj = ReportingEffortItem(**item_data)
        db.add(db_obj)
        await db.flush()  # Get the ID
        
        # Create type-specific details
        if obj_in.item_type == ItemType.TLF and tlf_details:
            tlf_obj = ReportingEffortTlfDetails(
                reporting_effort_item_id=db_obj.id,
                **tlf_details
            )
            db.add(tlf_obj)
        elif obj_in.item_type == ItemType.Dataset and dataset_details:
            dataset_obj = ReportingEffortDatasetDetails(
                reporting_effort_item_id=db_obj.id,
                **dataset_details
            )
            db.add(dataset_obj)
        
        # Create footnote associations
        if footnote_ids:
            for idx, footnote_id in enumerate(footnote_ids):
                footnote_assoc = ReportingEffortItemFootnote(
                    reporting_effort_item_id=db_obj.id,
                    footnote_id=footnote_id,
                    sequence_number=idx + 1
                )
                db.add(footnote_assoc)
        
        # Create acronym associations
        if acronym_ids:
            for acronym_id in acronym_ids:
                acronym_assoc = ReportingEffortItemAcronym(
                    reporting_effort_item_id=db_obj.id,
                    acronym_id=acronym_id
                )
                db.add(acronym_assoc)
        
        # Auto-create tracker entry
        if auto_create_tracker:
            tracker = ReportingEffortItemTracker(
                reporting_effort_item_id=db_obj.id
            )
            db.add(tracker)
        
        await db.commit()
        await db.refresh(db_obj)
        
        # Load all relationships
        return await self.get_with_details(db, id=db_obj.id)
    
    async def get(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[ReportingEffortItem]:
        """Get a single reporting effort item by ID."""
        result = await db.execute(
            select(ReportingEffortItem).where(ReportingEffortItem.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_with_details(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[ReportingEffortItem]:
        """Get a reporting effort item with all related details."""
        result = await db.execute(
            select(ReportingEffortItem)
            .options(
                selectinload(ReportingEffortItem.tlf_details),
                selectinload(ReportingEffortItem.dataset_details),
                selectinload(ReportingEffortItem.footnotes),
                selectinload(ReportingEffortItem.acronyms),
                selectinload(ReportingEffortItem.tracker)
            )
            .where(ReportingEffortItem.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportingEffortItem]:
        """Get multiple reporting effort items."""
        result = await db.execute(
            select(ReportingEffortItem)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_reporting_effort(
        self,
        db: AsyncSession,
        *,
        reporting_effort_id: int
    ) -> List[ReportingEffortItem]:
        """Get all items for a specific reporting effort."""
        result = await db.execute(
            select(ReportingEffortItem)
            .options(
                selectinload(ReportingEffortItem.tlf_details),
                selectinload(ReportingEffortItem.dataset_details),
                selectinload(ReportingEffortItem.footnotes),
                selectinload(ReportingEffortItem.acronyms),
                selectinload(ReportingEffortItem.tracker)
            )
            .where(ReportingEffortItem.reporting_effort_id == reporting_effort_id)
            .order_by(ReportingEffortItem.item_code)
        )
        return list(result.scalars().all())
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ReportingEffortItem,
        obj_in: ReportingEffortItemUpdate
    ) -> ReportingEffortItem:
        """Update a reporting effort item."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[ReportingEffortItem]:
        """
        Delete a reporting effort item.
        
        Note: Will cascade delete tracker, comments, and associations.
        """
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
    
    async def copy_from_package(
        self,
        db: AsyncSession,
        *,
        reporting_effort_id: int,
        package_id: int,
        item_ids: Optional[List[int]] = None
    ) -> List[ReportingEffortItem]:
        """
        Copy items from a package to a reporting effort.
        
        Args:
            db: Database session
            reporting_effort_id: Target reporting effort ID
            package_id: Source package ID
            item_ids: Optional list of specific item IDs to copy (None = copy all)
        
        Returns:
            List of created reporting effort items
        """
        from app.crud.package_item import package_item
        
        # Get package items
        package_items = await package_item.get_by_package(db, package_id=package_id)
        
        # Filter if specific items requested
        if item_ids:
            package_items = [item for item in package_items if item.id in item_ids]
        
        created_items = []
        for pkg_item in package_items:
            # Create reporting effort item
            item_data = ReportingEffortItemCreate(
                reporting_effort_id=reporting_effort_id,
                source_type="package",
                source_id=package_id,
                source_item_id=pkg_item.id,
                item_type=pkg_item.item_type,
                item_subtype=pkg_item.item_subtype,
                item_code=pkg_item.item_code,
                is_active=True
            )
            
            # Copy TLF details
            tlf_details = None
            if pkg_item.tlf_details:
                tlf_details = {
                    "title_id": pkg_item.tlf_details.title_id,
                    "population_flag_id": pkg_item.tlf_details.population_flag_id
                }
            
            # Copy dataset details
            dataset_details = None
            if pkg_item.dataset_details:
                dataset_details = {
                    "label": pkg_item.dataset_details.label,
                    "sorting_order": pkg_item.dataset_details.sorting_order,
                    "acronyms": pkg_item.dataset_details.acronyms
                }
            
            # Get footnote and acronym IDs
            footnote_ids = [f.footnote_id for f in pkg_item.footnotes] if pkg_item.footnotes else None
            acronym_ids = [a.acronym_id for a in pkg_item.acronyms] if pkg_item.acronyms else None
            
            # Create item with details
            created_item = await self.create_with_details(
                db,
                obj_in=item_data,
                tlf_details=tlf_details,
                dataset_details=dataset_details,
                footnote_ids=footnote_ids,
                acronym_ids=acronym_ids
            )
            created_items.append(created_item)
        
        return created_items
    
    async def copy_from_reporting_effort(
        self,
        db: AsyncSession,
        *,
        target_reporting_effort_id: int,
        source_reporting_effort_id: int,
        item_ids: Optional[List[int]] = None
    ) -> List[ReportingEffortItem]:
        """
        Copy items from another reporting effort.
        
        Args:
            db: Database session
            target_reporting_effort_id: Target reporting effort ID
            source_reporting_effort_id: Source reporting effort ID
            item_ids: Optional list of specific item IDs to copy (None = copy all)
        
        Returns:
            List of created reporting effort items
        """
        # Get source items
        source_items = await self.get_by_reporting_effort(
            db, 
            reporting_effort_id=source_reporting_effort_id
        )
        
        # Filter if specific items requested
        if item_ids:
            source_items = [item for item in source_items if item.id in item_ids]
        
        created_items = []
        for src_item in source_items:
            # Create new item
            item_data = ReportingEffortItemCreate(
                reporting_effort_id=target_reporting_effort_id,
                source_type="reporting_effort",
                source_id=source_reporting_effort_id,
                source_item_id=src_item.id,
                item_type=src_item.item_type,
                item_subtype=src_item.item_subtype,
                item_code=src_item.item_code,
                is_active=src_item.is_active
            )
            
            # Copy TLF details
            tlf_details = None
            if src_item.tlf_details:
                tlf_details = {
                    "title_id": src_item.tlf_details.title_id,
                    "population_flag_id": src_item.tlf_details.population_flag_id
                }
            
            # Copy dataset details
            dataset_details = None
            if src_item.dataset_details:
                dataset_details = {
                    "label": src_item.dataset_details.label,
                    "sorting_order": src_item.dataset_details.sorting_order,
                    "acronyms": src_item.dataset_details.acronyms
                }
            
            # Get footnote and acronym IDs
            footnote_ids = [f.footnote_id for f in src_item.footnotes] if src_item.footnotes else None
            acronym_ids = [a.acronym_id for a in src_item.acronyms] if src_item.acronyms else None
            
            # Create item with details
            created_item = await self.create_with_details(
                db,
                obj_in=item_data,
                tlf_details=tlf_details,
                dataset_details=dataset_details,
                footnote_ids=footnote_ids,
                acronym_ids=acronym_ids
            )
            created_items.append(created_item)
        
        return created_items
    
    async def check_deletion_protection(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[str]:
        """
        Check if item can be deleted based on tracker assignment.
        
        Returns:
            None if can be deleted, error message if protected
        """
        # Get tracker
        result = await db.execute(
            select(ReportingEffortItemTracker)
            .where(ReportingEffortItemTracker.reporting_effort_item_id == id)
        )
        tracker = result.scalar_one_or_none()
        
        if tracker and (tracker.production_programmer_id or tracker.qc_programmer_id):
            return "Cannot delete item: programmers are assigned to this item"
        
        return None


# Create singleton instance
reporting_effort_item = ReportingEffortItemCRUD()