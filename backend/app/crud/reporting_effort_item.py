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
from app.models.enums import ItemType, SourceType
from app.schemas.reporting_effort_item import (
    ReportingEffortItemCreate,
    ReportingEffortItemUpdate,
    ReportingEffortItemCreateWithDetails
)


class ReportingEffortItemCRUD:
    """CRUD operations for ReportingEffortItem."""
    
    async def create(self, db: AsyncSession, *, obj_in: ReportingEffortItemCreate) -> ReportingEffortItem:
        """Create a new reporting effort item."""
        # Check for duplicate
        existing = await self.get_by_unique_key(
            db,
            reporting_effort_id=obj_in.reporting_effort_id,
            item_type=obj_in.item_type,
            item_subtype=obj_in.item_subtype,
            item_code=obj_in.item_code
        )
        if existing:
            raise ValueError(f"A {obj_in.item_type} with code {obj_in.item_code} already exists in this reporting effort")
        
        # With unified str,Enum, we can pass directly
        db_obj = ReportingEffortItem(
            reporting_effort_id=obj_in.reporting_effort_id,
            source_type=obj_in.source_type,
            source_id=obj_in.source_id,
            source_item_id=obj_in.source_item_id,
            item_type=obj_in.item_type,
            item_subtype=obj_in.item_subtype,
            item_code=obj_in.item_code,
            is_active=obj_in.is_active
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def create_with_details(
        self,
        db: AsyncSession,
        *,
        obj_in: ReportingEffortItemCreateWithDetails,
        auto_create_tracker: bool = True
    ) -> ReportingEffortItem:
        """
        Create a reporting effort item with all related details.
        
        Args:
            db: Database session
            obj_in: Item creation data with details
            auto_create_tracker: Whether to auto-create tracker entry
        
        Returns:
            Created item with all relationships
        """
        # Check for duplicate
        existing = await self.get_by_unique_key(
            db,
            reporting_effort_id=obj_in.reporting_effort_id,
            item_type=obj_in.item_type,
            item_subtype=obj_in.item_subtype,
            item_code=obj_in.item_code
        )
        if existing:
            raise ValueError(f"A {obj_in.item_type} with code {obj_in.item_code} already exists in this reporting effort")
        # Create the main reporting effort item
        # With unified str,Enum, we can pass directly
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"About to create ReportingEffortItem with:")
        logger.info(f"  source_type: '{obj_in.source_type}' (type: {type(obj_in.source_type)})")
        logger.info(f"  item_type: '{obj_in.item_type}' (type: {type(obj_in.item_type)})")
        
        try:
            db_obj = ReportingEffortItem(
                reporting_effort_id=obj_in.reporting_effort_id,
                source_type=obj_in.source_type,
                source_id=obj_in.source_id,
                source_item_id=obj_in.source_item_id,
                item_type=obj_in.item_type,
                item_subtype=obj_in.item_subtype,
                item_code=obj_in.item_code,
                is_active=obj_in.is_active
            )
            logger.info(f"Successfully created ReportingEffortItem object")
            
            db.add(db_obj)
            logger.info(f"Added to database session")
            
            await db.flush()  # Get the ID without committing
            logger.info(f"Flushed to database, item ID: {db_obj.id}")
            
        except Exception as db_error:
            logger.error(f"Error creating ReportingEffortItem: {str(db_error)}", exc_info=True)
            raise
        
        # Create TLF details if provided and item is TLF
        if obj_in.item_type == ItemType.TLF and obj_in.tlf_details:
            tlf_details = ReportingEffortTlfDetails(
                reporting_effort_item_id=db_obj.id,
                title_id=obj_in.tlf_details.title_id,
                population_flag_id=obj_in.tlf_details.population_flag_id,
                ich_category_id=getattr(obj_in.tlf_details, 'ich_category_id', None)
            )
            db.add(tlf_details)
        
        # Create Dataset details if provided and item is Dataset
        elif obj_in.item_type == ItemType.Dataset and obj_in.dataset_details:
            dataset_details = ReportingEffortDatasetDetails(
                reporting_effort_item_id=db_obj.id,
                label=obj_in.dataset_details.label,
                sorting_order=obj_in.dataset_details.sorting_order,
                acronyms=obj_in.dataset_details.acronyms
            )
            db.add(dataset_details)
        
        # Create footnote associations
        for footnote in obj_in.footnotes:
            footnote_assoc = ReportingEffortItemFootnote(
                reporting_effort_item_id=db_obj.id,
                footnote_id=footnote.footnote_id,
                sequence_number=footnote.sequence_number
            )
            db.add(footnote_assoc)
        
        # Create acronym associations
        for acronym in obj_in.acronyms:
            acronym_assoc = ReportingEffortItemAcronym(
                reporting_effort_item_id=db_obj.id,
                acronym_id=acronym.acronym_id
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
        result = await db.execute(
            select(ReportingEffortItem)
            .options(
                selectinload(ReportingEffortItem.tlf_details),
                selectinload(ReportingEffortItem.dataset_details),
                selectinload(ReportingEffortItem.footnotes),
                selectinload(ReportingEffortItem.acronyms),
                selectinload(ReportingEffortItem.tracker)
            )
            .where(ReportingEffortItem.id == db_obj.id)
        )
        return result.scalar_one()
    
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
    
    async def get_by_unique_key(
        self, db: AsyncSession, *, 
        reporting_effort_id: int, 
        item_type: str,
        item_subtype: str,
        item_code: str
    ) -> Optional[ReportingEffortItem]:
        """Get a reporting effort item by its unique key combination."""
        result = await db.execute(
            select(ReportingEffortItem).where(
                and_(
                    ReportingEffortItem.reporting_effort_id == reporting_effort_id,
                    ReportingEffortItem.item_type == item_type,
                    ReportingEffortItem.item_subtype == item_subtype,
                    ReportingEffortItem.item_code == item_code
                )
            )
        )
        return result.scalar_one_or_none()
    
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
        
        # Reload with relationships
        result = await db.execute(
            select(ReportingEffortItem)
            .options(
                selectinload(ReportingEffortItem.tlf_details),
                selectinload(ReportingEffortItem.dataset_details),
                selectinload(ReportingEffortItem.footnotes),
                selectinload(ReportingEffortItem.acronyms),
                selectinload(ReportingEffortItem.tracker)
            )
            .where(ReportingEffortItem.id == db_obj.id)
        )
        return result.scalar_one()
    
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
        db_obj = await self.get_with_details(db, id=id)
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
            
            # Delete tracker if exists
            if db_obj.tracker:
                await db.delete(db_obj.tracker)
            
            # Delete the item itself
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
        package_items = await package_item.get_by_package_id(db, package_id=package_id)
        
        # Filter if specific items requested
        if item_ids:
            package_items = [item for item in package_items if item.id in item_ids]
        
        created_items = []
        for pkg_item in package_items:
            # Create reporting effort item - not used anymore, can be removed
            # item_data = ReportingEffortItemCreate(...)
            
            # Build the complete item data with details
            from app.schemas.reporting_effort_item import (
                ReportingEffortItemCreateWithDetails,
                ReportingEffortTlfDetailsCreate,
                ReportingEffortDatasetDetailsCreate,
                ReportingEffortItemFootnoteCreate,
                ReportingEffortItemAcronymCreate
            )
            
            # Prepare TLF details if applicable
            tlf_details = None
            if pkg_item.item_type == ItemType.TLF and pkg_item.tlf_details:
                tlf_details = ReportingEffortTlfDetailsCreate(
                    title_id=pkg_item.tlf_details.title_id,
                    population_flag_id=pkg_item.tlf_details.population_flag_id,
                    ich_category_id=getattr(pkg_item.tlf_details, 'ich_category_id', None)
                )
            
            # Prepare dataset details if applicable
            dataset_details = None
            if pkg_item.item_type == ItemType.Dataset and pkg_item.dataset_details:
                dataset_details = ReportingEffortDatasetDetailsCreate(
                    label=pkg_item.dataset_details.label,
                    sorting_order=pkg_item.dataset_details.sorting_order,
                    acronyms=pkg_item.dataset_details.acronyms
                )
            
            # Prepare footnotes
            footnotes = []
            if pkg_item.footnotes:
                for idx, f in enumerate(pkg_item.footnotes):
                    footnotes.append(ReportingEffortItemFootnoteCreate(
                        footnote_id=f.footnote_id,
                        sequence_number=getattr(f, 'sequence_number', idx + 1)
                    ))
            
            # Prepare acronyms
            acronyms = []
            if pkg_item.acronyms:
                for a in pkg_item.acronyms:
                    acronyms.append(ReportingEffortItemAcronymCreate(
                        acronym_id=a.acronym_id
                    ))
            
            # Create complete item data with details
            # Always pass string values for enums
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"About to create ReportingEffortItemCreateWithDetails")
            logger.info(f"pkg_item.item_type = {pkg_item.item_type} (type={type(pkg_item.item_type)})")
            
            item_data_with_details = ReportingEffortItemCreateWithDetails(
                reporting_effort_id=reporting_effort_id,
                source_type=SourceType.PACKAGE.value,  # Use enum value
                source_id=package_id,
                source_item_id=pkg_item.id,
                item_type=pkg_item.item_type.value,
                item_subtype=pkg_item.item_subtype,
                item_code=pkg_item.item_code,
                is_active=True,
                tlf_details=tlf_details,
                dataset_details=dataset_details,
                footnotes=footnotes,
                acronyms=acronyms
            )
            
            logger.info(f"Created ReportingEffortItemCreateWithDetails, calling create_with_details")
            logger.info(f"Schema validation passed - source_type: '{item_data_with_details.source_type}' (type: {type(item_data_with_details.source_type)})")
            logger.info(f"Schema validation passed - item_type: '{item_data_with_details.item_type}' (type: {type(item_data_with_details.item_type)})")
            
            try:
                # Create item with details
                created_item = await self.create_with_details(
                    db,
                    obj_in=item_data_with_details,
                    auto_create_tracker=True
                )
                logger.info(f"Successfully created item with ID: {created_item.id}")
                created_items.append(created_item)
            except Exception as create_error:
                logger.error(f"Error in create_with_details for item {pkg_item.item_code}: {str(create_error)}", exc_info=True)
                raise
        
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
            # Create new item - not used anymore, can be removed
            # item_data = ReportingEffortItemCreate(...)
            
            # Build the complete item data with details
            from app.schemas.reporting_effort_item import (
                ReportingEffortItemCreateWithDetails,
                ReportingEffortTlfDetailsCreate,
                ReportingEffortDatasetDetailsCreate,
                ReportingEffortItemFootnoteCreate,
                ReportingEffortItemAcronymCreate
            )
            
            # Prepare TLF details if applicable
            tlf_details = None
            if src_item.item_type == ItemType.TLF and src_item.tlf_details:
                tlf_details = ReportingEffortTlfDetailsCreate(
                    title_id=src_item.tlf_details.title_id,
                    population_flag_id=src_item.tlf_details.population_flag_id,
                    ich_category_id=getattr(src_item.tlf_details, 'ich_category_id', None)
                )
            
            # Prepare dataset details if applicable
            dataset_details = None
            if src_item.item_type == ItemType.Dataset and src_item.dataset_details:
                dataset_details = ReportingEffortDatasetDetailsCreate(
                    label=src_item.dataset_details.label,
                    sorting_order=src_item.dataset_details.sorting_order,
                    acronyms=src_item.dataset_details.acronyms
                )
            
            # Prepare footnotes
            footnotes = []
            if src_item.footnotes:
                for idx, f in enumerate(src_item.footnotes):
                    footnotes.append(ReportingEffortItemFootnoteCreate(
                        footnote_id=f.footnote_id,
                        sequence_number=getattr(f, 'sequence_number', idx + 1)
                    ))
            
            # Prepare acronyms
            acronyms = []
            if src_item.acronyms:
                for a in src_item.acronyms:
                    acronyms.append(ReportingEffortItemAcronymCreate(
                        acronym_id=a.acronym_id
                    ))
            
            # Create complete item data with details
            # Always pass string values for enums
            item_data_with_details = ReportingEffortItemCreateWithDetails(
                reporting_effort_id=target_reporting_effort_id,
                source_type=SourceType.REPORTING_EFFORT.value,  # Use enum value
                source_id=source_reporting_effort_id,
                source_item_id=src_item.id,
                item_type=src_item.item_type.value,
                item_subtype=src_item.item_subtype,
                item_code=src_item.item_code,
                is_active=src_item.is_active,
                tlf_details=tlf_details,
                dataset_details=dataset_details,
                footnotes=footnotes,
                acronyms=acronyms
            )
            
            # Create item with details
            created_item = await self.create_with_details(
                db,
                obj_in=item_data_with_details,
                auto_create_tracker=True
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