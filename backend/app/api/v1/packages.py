"""Packages API endpoints."""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.crud import package, package_item, text_element
from app.db.session import get_db
from app.schemas.package import Package, PackageCreate, PackageUpdate, PackageWithItems
from app.schemas.package_item import (
    PackageItem, PackageItemCreate, PackageItemUpdate, 
    PackageItemCreateWithDetails, PackageTlfDetailsCreate,
    PackageDatasetDetailsCreate, ItemTypeEnum
)
from app.schemas.text_element import TextElementCreate
from app.models.text_element import TextElementType
from app.api.v1.websocket import (
    broadcast_package_created, broadcast_package_updated, broadcast_package_deleted,
    broadcast_package_item_created, broadcast_package_item_updated, broadcast_package_item_deleted
)

router = APIRouter()


# Package endpoints
@router.post("/", response_model=Package, status_code=status.HTTP_201_CREATED)
async def create_package(
    *,
    db: AsyncSession = Depends(get_db),
    package_in: PackageCreate,
) -> Package:
    """
    Create a new package.
    """
    try:
        # Check if package with same name already exists
        existing_package = await package.get_by_name(db, package_name=package_in.package_name)
        if existing_package:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Package with this name already exists"
            )
        
        created_package = await package.create(db, obj_in=package_in)
        print(f"Package created successfully: {created_package.package_name} (ID: {created_package.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"About to broadcast package_created...")
            await broadcast_package_created(created_package)
            print(f"Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")
        
        return created_package
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create package"
        )


@router.get("/", response_model=List[Package])
async def read_packages(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[Package]:
    """
    Retrieve packages with pagination.
    """
    try:
        return await package.get_multi(db, skip=skip, limit=limit)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve packages"
        )


@router.get("/{package_id}", response_model=PackageWithItems)
async def read_package(
    *,
    db: AsyncSession = Depends(get_db),
    package_id: int,
) -> PackageWithItems:
    """
    Get a specific package by ID with its items.
    """
    try:
        db_package = await package.get(db, id=package_id)
        if not db_package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Get package items
        items = await package_item.get_by_package_id(db, package_id=package_id)
        
        # Convert to schema with items
        package_dict = {
            "id": db_package.id,
            "package_name": db_package.package_name,
            "created_at": db_package.created_at,
            "updated_at": db_package.updated_at,
            "package_items": items
        }
        
        return PackageWithItems(**package_dict)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve package"
        )


@router.put("/{package_id}", response_model=Package)
async def update_package(
    *,
    db: AsyncSession = Depends(get_db),
    package_id: int,
    package_in: PackageUpdate,
) -> Package:
    """
    Update an existing package.
    """
    try:
        db_package = await package.get(db, id=package_id)
        if not db_package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Check if new name already exists (if name is being changed)
        if package_in.package_name != db_package.package_name:
            existing_package = await package.get_by_name(db, package_name=package_in.package_name)
            if existing_package:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Package with this name already exists"
                )
        
        updated_package = await package.update(db, db_obj=db_package, obj_in=package_in)
        print(f"Package updated successfully: {updated_package.package_name} (ID: {updated_package.id})")
        
        # Broadcast WebSocket event
        try:
            await broadcast_package_updated(updated_package)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return updated_package
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update package"
        )


@router.delete("/{package_id}", response_model=Package)
async def delete_package(
    *,
    db: AsyncSession = Depends(get_db),
    package_id: int,
) -> Package:
    """
    Delete a package.
    """
    try:
        db_package = await package.get(db, id=package_id)
        if not db_package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Check for associated package items before deletion
        associated_items = await package_item.get_by_package_id(db, package_id=package_id)
        if associated_items:
            item_codes = [item.item_code for item in associated_items[:5]]  # Show first 5
            more_count = len(associated_items) - 5 if len(associated_items) > 5 else 0
            detail_msg = f"Cannot delete package '{db_package.package_name}': {len(associated_items)} associated item(s) exist"
            if item_codes:
                detail_msg += f": {', '.join(item_codes)}"
                if more_count > 0:
                    detail_msg += f" and {more_count} more"
            detail_msg += ". Please delete all associated items first."
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail_msg
            )
        
        deleted_package = await package.delete(db, id=package_id)
        print(f"Package deleted successfully: {deleted_package.package_name} (ID: {deleted_package.id})")
        
        # Broadcast WebSocket event
        try:
            await broadcast_package_deleted(deleted_package)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return deleted_package
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete package"
        )


# Package Item endpoints
@router.post("/{package_id}/items", response_model=PackageItem, status_code=status.HTTP_201_CREATED)
async def create_package_item(
    *,
    db: AsyncSession = Depends(get_db),
    package_id: int,
    item_in: PackageItemCreateWithDetails,
) -> PackageItem:
    """
    Create a new package item with all details.
    """
    try:
        # Verify package exists
        db_package = await package.get(db, id=package_id)
        if not db_package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Check for duplicate item (moved to CRUD layer but also check here for better error message)
        existing_item = await package_item.get_by_unique_key(
            db,
            package_id=package_id,
            item_type=item_in.item_type.value,
            item_subtype=item_in.item_subtype,
            item_code=item_in.item_code
        )
        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A {item_in.item_type.value} with code '{item_in.item_code}' already exists in this package"
            )
        
        # Ensure package_id matches
        item_in.package_id = package_id
        
        created_item = await package_item.create_with_details(db, obj_in=item_in)
        print(f"Package item created successfully: {created_item.item_code} (ID: {created_item.id})")
        
        # Broadcast WebSocket event
        try:
            await broadcast_package_item_created(created_item)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return created_item
    except ValueError as e:
        # Handle duplicate error from CRUD
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create package item"
        )


@router.get("/{package_id}/items", response_model=List[PackageItem])
async def read_package_items(
    *,
    db: AsyncSession = Depends(get_db),
    package_id: int,
) -> List[PackageItem]:
    """
    Get all items for a specific package.
    """
    try:
        # Verify package exists
        db_package = await package.get(db, id=package_id)
        if not db_package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        return await package_item.get_by_package_id(db, package_id=package_id)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve package items"
        )


@router.get("/items/{item_id}", response_model=PackageItem)
async def read_package_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
) -> PackageItem:
    """
    Get a specific package item by ID.
    """
    try:
        db_item = await package_item.get(db, id=item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package item not found"
            )
        return db_item
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve package item"
        )


@router.put("/items/{item_id}", response_model=PackageItem)
async def update_package_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
    item_in: PackageItemUpdate,
) -> PackageItem:
    """
    Update an existing package item.
    """
    try:
        print(f"Updating package item {item_id} with data: {item_in.model_dump(exclude_unset=True)}")
        
        db_item = await package_item.get(db, id=item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package item not found"
            )
        
        updated_item = await package_item.update(db, db_obj=db_item, obj_in=item_in)
        print(f"Package item updated successfully: {updated_item.item_code} (ID: {updated_item.id})")
        
        # Broadcast WebSocket event
        try:
            await broadcast_package_item_updated(updated_item)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return updated_item
    except Exception as e:
        print(f"Error updating package item {item_id}: {e}")
        if isinstance(e, HTTPException):
            raise
        # Return more detailed error information
        error_detail = f"Failed to update package item: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.delete("/items/{item_id}", response_model=PackageItem)
async def delete_package_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
) -> PackageItem:
    """
    Delete a package item.
    """
    try:
        db_item = await package_item.get(db, id=item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package item not found"
            )
        
        deleted_item = await package_item.delete(db, id=item_id)
        print(f"Package item deleted successfully: {deleted_item.item_code} (ID: {deleted_item.id})")
        
        # Broadcast WebSocket event
        try:
            await broadcast_package_item_deleted(deleted_item)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return deleted_item
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete package item"
        )


# Bulk Upload Schemas
class BulkTLFItem(BaseModel):
    """Schema for bulk TLF upload."""
    item_subtype: str = Field(..., description="Table/Listing/Figure")
    item_code: str = Field(..., description="TLF code, e.g., t14.1.1")
    title: str = Field(..., description="Title text")
    footnotes: List[str] = Field(default_factory=list, description="List of footnote texts")
    population_flag: Optional[str] = Field(None, description="Population flag text")
    acronyms: List[str] = Field(default_factory=list, description="List of acronym texts")
    ich_category: Optional[str] = Field(None, description="ICH category text")


class BulkDatasetItem(BaseModel):
    """Schema for bulk dataset upload."""
    item_subtype: str = Field(..., description="SDTM/ADaM")
    item_code: str = Field(..., description="Dataset name, e.g., DM")
    label: Optional[str] = Field(None, description="Dataset label")
    sorting_order: Optional[int] = Field(None, description="Display order")


class BulkUploadResponse(BaseModel):
    """Response for bulk upload operations."""
    success: bool
    created_count: int
    errors: List[str] = Field(default_factory=list)
    items: List[PackageItem] = Field(default_factory=list)


# Bulk Upload Endpoints
@router.post("/{package_id}/items/bulk-tlf", response_model=BulkUploadResponse)
async def bulk_create_tlf_items(
    *,
    db: AsyncSession = Depends(get_db),
    package_id: int,
    items_in: List[BulkTLFItem],
) -> BulkUploadResponse:
    """
    Bulk create TLF items for a package.
    Creates text elements if they don't exist.
    """
    errors = []
    created_items = []
    
    try:
        # Verify package exists
        db_package = await package.get(db, id=package_id)
        if not db_package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Validate all items first
        for idx, item in enumerate(items_in):
            # Validate subtype
            if item.item_subtype not in ['Table', 'Listing', 'Figure']:
                errors.append(f"Item {idx+1}: Invalid TLF type '{item.item_subtype}'. Must be Table, Listing, or Figure")
            
            # Check for duplicates
            existing = await package_item.get_by_unique_key(
                db,
                package_id=package_id,
                item_type="TLF",
                item_subtype=item.item_subtype,
                item_code=item.item_code
            )
            if existing:
                errors.append(f"Item {idx+1}: TLF '{item.item_code}' already exists in this package")
        
        # If validation errors, return early
        if errors:
            return BulkUploadResponse(
                success=False,
                created_count=0,
                errors=errors,
                items=[]
            )
        
        # Process each item
        for item in items_in:
            try:
                # Get or create text elements
                title_id = None
                if item.title:
                    title_elem = await text_element.get_by_type_and_label(
                        db, type=TextElementType.title, label=item.title
                    )
                    if not title_elem:
                        title_elem = await text_element.create(
                            db, obj_in=TextElementCreate(type=TextElementType.title, label=item.title)
                        )
                    title_id = title_elem.id
                
                population_flag_id = None
                if item.population_flag:
                    pop_elem = await text_element.get_by_type_and_label(
                        db, type=TextElementType.population_set, label=item.population_flag
                    )
                    if not pop_elem:
                        pop_elem = await text_element.create(
                            db, obj_in=TextElementCreate(type=TextElementType.population_set, label=item.population_flag)
                        )
                    population_flag_id = pop_elem.id
                
                ich_category_id = None
                if item.ich_category:
                    ich_elem = await text_element.get_by_type_and_label(
                        db, type=TextElementType.ich_category, label=item.ich_category
                    )
                    if not ich_elem:
                        ich_elem = await text_element.create(
                            db, obj_in=TextElementCreate(type=TextElementType.ich_category, label=item.ich_category)
                        )
                    ich_category_id = ich_elem.id
                
                # Process footnotes
                footnote_ids = []
                for footnote_text in item.footnotes:
                    fn_elem = await text_element.get_by_type_and_label(
                        db, type=TextElementType.footnote, label=footnote_text
                    )
                    if not fn_elem:
                        fn_elem = await text_element.create(
                            db, obj_in=TextElementCreate(type=TextElementType.footnote, label=footnote_text)
                        )
                    footnote_ids.append(fn_elem.id)
                
                # Process acronyms
                acronym_ids = []
                for acronym_text in item.acronyms:
                    ac_elem = await text_element.get_by_type_and_label(
                        db, type=TextElementType.acronyms_set, label=acronym_text
                    )
                    if not ac_elem:
                        ac_elem = await text_element.create(
                            db, obj_in=TextElementCreate(type=TextElementType.acronyms_set, label=acronym_text)
                        )
                    acronym_ids.append(ac_elem.id)
                
                # Create package item with details
                item_create = PackageItemCreateWithDetails(
                    package_id=package_id,
                    item_type=ItemTypeEnum.TLF,
                    item_subtype=item.item_subtype,
                    item_code=item.item_code,
                    tlf_details=PackageTlfDetailsCreate(
                        title_id=title_id,
                        population_flag_id=population_flag_id,
                        ich_category_id=ich_category_id
                    ),
                    footnotes=[{"footnote_id": fid, "sequence_number": idx+1} 
                              for idx, fid in enumerate(footnote_ids)],
                    acronyms=[{"acronym_id": aid} for aid in acronym_ids]
                )
                
                created_item = await package_item.create_with_details(db, obj_in=item_create)
                # Convert to Pydantic model for response
                created_items.append(PackageItem.model_validate(created_item))
                
                # Broadcast WebSocket event
                try:
                    await broadcast_package_item_created(created_item)
                except Exception:
                    pass  # Don't fail on broadcast error
                    
            except Exception as e:
                errors.append(f"Failed to create TLF '{item.item_code}': {str(e)}")
        
        return BulkUploadResponse(
            success=len(errors) == 0,
            created_count=len(created_items),
            errors=errors,
            items=created_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk upload failed: {str(e)}"
        )


@router.post("/{package_id}/items/bulk-dataset", response_model=BulkUploadResponse)
async def bulk_create_dataset_items(
    *,
    db: AsyncSession = Depends(get_db),
    package_id: int,
    items_in: List[BulkDatasetItem],
) -> BulkUploadResponse:
    """
    Bulk create dataset items for a package.
    """
    errors = []
    created_items = []
    
    try:
        # Verify package exists
        db_package = await package.get(db, id=package_id)
        if not db_package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Validate all items first
        for idx, item in enumerate(items_in):
            # Validate subtype
            if item.item_subtype not in ['SDTM', 'ADaM']:
                errors.append(f"Item {idx+1}: Invalid dataset type '{item.item_subtype}'. Must be SDTM or ADaM")
            
            # Check for duplicates
            existing = await package_item.get_by_unique_key(
                db,
                package_id=package_id,
                item_type="Dataset",
                item_subtype=item.item_subtype,
                item_code=item.item_code
            )
            if existing:
                errors.append(f"Item {idx+1}: Dataset '{item.item_code}' already exists in this package")
        
        # If validation errors, return early
        if errors:
            return BulkUploadResponse(
                success=False,
                created_count=0,
                errors=errors,
                items=[]
            )
        
        # Process each item
        for item in items_in:
            try:
                # Create package item with dataset details
                item_create = PackageItemCreateWithDetails(
                    package_id=package_id,
                    item_type=ItemTypeEnum.Dataset,
                    item_subtype=item.item_subtype,
                    item_code=item.item_code,
                    dataset_details=PackageDatasetDetailsCreate(
                        label=item.label,
                        sorting_order=item.sorting_order,
                        acronyms=None  # Could be extended to support acronyms JSON
                    ),
                    footnotes=[],
                    acronyms=[]
                )
                
                created_item = await package_item.create_with_details(db, obj_in=item_create)
                # Convert to Pydantic model for response
                created_items.append(PackageItem.model_validate(created_item))
                
                # Broadcast WebSocket event
                try:
                    await broadcast_package_item_created(created_item)
                except Exception:
                    pass  # Don't fail on broadcast error
                    
            except Exception as e:
                errors.append(f"Failed to create dataset '{item.item_code}': {str(e)}")
        
        return BulkUploadResponse(
            success=len(errors) == 0,
            created_count=len(created_items),
            errors=errors,
            items=created_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk upload failed: {str(e)}"
        )