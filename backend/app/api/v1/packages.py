"""Packages API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import package, package_item, study
from app.db.session import get_db
from app.schemas.package import Package, PackageCreate, PackageUpdate, PackageWithItems
from app.schemas.package_item import (
    PackageItem, PackageItemCreate, PackageItemUpdate, 
    PackageItemCreateWithDetails
)
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
        print(f"✅ Package created successfully: {created_package.package_name} (ID: {created_package.id})")
        
        # Broadcast WebSocket event for real-time updates
        try:
            print(f"🚀 About to broadcast package_created...")
            await broadcast_package_created(created_package)
            print(f"✅ Broadcast completed successfully")
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
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
        print(f"✅ Package updated successfully: {updated_package.package_name} (ID: {updated_package.id})")
        
        # Broadcast WebSocket event
        try:
            await broadcast_package_updated(updated_package)
        except Exception as ws_error:
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
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
        print(f"✅ Package deleted successfully: {deleted_package.package_name} (ID: {deleted_package.id})")
        
        # Broadcast WebSocket event
        try:
            await broadcast_package_deleted(deleted_package)
        except Exception as ws_error:
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
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
        
        # Verify study exists
        db_study = await study.get(db, id=item_in.study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study not found"
            )
        
        # Check for duplicate item
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
                detail=f"Package item with type={item_in.item_type.value}, subtype={item_in.item_subtype}, code={item_in.item_code} already exists in this package"
            )
        
        # Ensure package_id matches
        item_in.package_id = package_id
        
        created_item = await package_item.create_with_details(db, obj_in=item_in)
        print(f"✅ Package item created successfully: {created_item.item_code} (ID: {created_item.id})")
        
        # Broadcast WebSocket event
        try:
            await broadcast_package_item_created(created_item)
        except Exception as ws_error:
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return created_item
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
        db_item = await package_item.get(db, id=item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package item not found"
            )
        
        updated_item = await package_item.update(db, db_obj=db_item, obj_in=item_in)
        print(f"✅ Package item updated successfully: {updated_item.item_code} (ID: {updated_item.id})")
        
        # Broadcast WebSocket event
        try:
            await broadcast_package_item_updated(updated_item)
        except Exception as ws_error:
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return updated_item
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update package item"
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
        print(f"✅ Package item deleted successfully: {deleted_item.item_code} (ID: {deleted_item.id})")
        
        # Broadcast WebSocket event
        try:
            await broadcast_package_item_deleted(deleted_item)
        except Exception as ws_error:
            print(f"❌ WebSocket broadcast error: {ws_error}")
        
        return deleted_item
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete package item"
        )