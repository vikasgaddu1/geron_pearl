"""Reporting Effort Items API endpoints."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.crud import reporting_effort_item, reporting_effort, audit_log

logger = logging.getLogger(__name__)
from app.crud.package_item import package_item
from app.db.session import get_db
from app.schemas.reporting_effort_item import (
    ReportingEffortItem, 
    ReportingEffortItemCreate, 
    ReportingEffortItemUpdate,
    ReportingEffortItemWithDetails
)
from app.models.reporting_effort_item import ItemType, SourceType
from app.models.user import UserRole
from app.utils import sqlalchemy_to_dict
from app.api.v1.websocket import manager

# WebSocket broadcasting functions
async def broadcast_reporting_effort_item_created(item_data):
    """Broadcast that a new reporting effort item was created."""
    try:
        from app.utils import broadcast_message
        message = broadcast_message("reporting_effort_item_created", sqlalchemy_to_dict(item_data))
        await manager.broadcast(message)
    except Exception as e:
        logger.error(f"WebSocket broadcast error: {e}")

async def broadcast_reporting_effort_item_updated(item_data):
    """Broadcast that a reporting effort item was updated."""
    try:
        from app.utils import broadcast_message
        message = broadcast_message("reporting_effort_item_updated", sqlalchemy_to_dict(item_data))
        await manager.broadcast(message)
    except Exception as e:
        logger.error(f"WebSocket broadcast error: {e}")

async def broadcast_reporting_effort_item_deleted(item_data):
    """Broadcast that a reporting effort item was deleted."""
    try:
        from app.utils import broadcast_message
        message = broadcast_message("reporting_effort_item_deleted", sqlalchemy_to_dict(item_data))
        await manager.broadcast(message)
    except Exception as e:
        logger.error(f"WebSocket broadcast error: {e}")

router = APIRouter()

# Bulk Upload Schemas
class BulkTLFItem(BaseModel):
    """Schema for bulk TLF upload."""
    item_subtype: str = Field(..., description="Table/Listing/Figure")
    item_code: str = Field(..., description="TLF code, e.g., t14.1.1")
    title: Optional[str] = Field(None, description="Title text")
    footnotes: List[str] = Field(default_factory=list, description="List of footnote texts")
    population_flag: Optional[str] = Field(None, description="Population flag text")
    acronyms: List[str] = Field(default_factory=list, description="List of acronym texts")

class BulkDatasetItem(BaseModel):
    """Schema for bulk dataset upload."""
    item_subtype: str = Field(..., description="SDTM/ADaM")
    item_code: str = Field(..., description="Dataset name, e.g., DM")
    label: Optional[str] = Field(None, description="Dataset label")
    acronyms: Optional[str] = Field(None, description="Acronyms JSON string")

class BulkUploadResponse(BaseModel):
    """Response for bulk upload operations."""
    success: bool
    created_count: int
    errors: List[str] = Field(default_factory=list)
    items: List[ReportingEffortItem] = Field(default_factory=list)

class CopyFromPackageRequest(BaseModel):
    """Request schema for copying items from a package."""
    package_id: int = Field(..., description="ID of the source package")
    item_ids: Optional[List[int]] = Field(None, description="Specific item IDs to copy (None = copy all)")

class CopyFromReportingEffortRequest(BaseModel):
    """Request schema for copying items from another reporting effort."""
    source_reporting_effort_id: int = Field(..., description="ID of the source reporting effort")
    item_ids: Optional[List[int]] = Field(None, description="Specific item IDs to copy (None = copy all)")

# CRUD Endpoints
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_reporting_effort_item(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    item_in: ReportingEffortItemCreate,
) -> dict:
    """
    Create a new reporting effort item.
    Automatically creates a tracker entry.
    """
    try:
        # Verify reporting effort exists
        db_effort = await reporting_effort.get(db, id=item_in.reporting_effort_id)
        if not db_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )
        
        # Check for duplicate item
        # This will be handled by the unique constraint in the model
        # But we can provide better error messages here
        
        # Use simple create instead of create_with_details for debugging
        created_item = await reporting_effort_item.create_with_details(
            db,
            obj_in=item_in,
            auto_create_tracker=True
        )
        # Get simple object without relationships
        simple_item = await reporting_effort_item.get(db, id=created_item.id)
        
        logger.info(f"Reporting effort item created successfully: {created_item.item_code} (ID: {created_item.id})")
        
        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_items",
                record_id=created_item.id,
                action="CREATE",
                user_id=getattr(request.state, 'user_id', None),
                changes={"created": sqlalchemy_to_dict(created_item)},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            logger.error(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket event (temporarily disabled for debugging)
        try:
            # await broadcast_reporting_effort_item_created(created_item)
            print("WebSocket broadcast temporarily disabled for debugging")
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        # Return a simple dict response to avoid serialization issues
        return {
            "id": created_item.id,
            "reporting_effort_id": created_item.reporting_effort_id,
            "source_type": created_item.source_type.value if created_item.source_type else None,
            "source_id": created_item.source_id,
            "source_item_id": created_item.source_item_id,
            "item_type": created_item.item_type.value,
            "item_subtype": created_item.item_subtype,
            "item_code": created_item.item_code,
            "is_active": created_item.is_active,
            "created_at": created_item.created_at.isoformat(),
            "updated_at": created_item.updated_at.isoformat() if created_item.updated_at else None
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reporting effort item: {str(e)}"
        )

@router.get("/", response_model=List[ReportingEffortItem])
async def read_reporting_effort_items(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[ReportingEffortItem]:
    """
    Retrieve reporting effort items with pagination.
    """
    try:
        return await reporting_effort_item.get_multi(db, skip=skip, limit=limit)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reporting effort items"
        )

@router.get("/{item_id}", response_model=dict)
async def read_reporting_effort_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
) -> dict:
    """
    Get a specific reporting effort item by ID with all details.
    """
    try:
        db_item = await reporting_effort_item.get_with_details(db, id=item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort item not found"
            )
        # Return dict to avoid serialization issues
        return {
            "id": db_item.id,
            "reporting_effort_id": db_item.reporting_effort_id,
            "source_type": db_item.source_type.value if db_item.source_type else None,
            "source_id": db_item.source_id,
            "source_item_id": db_item.source_item_id,
            "item_type": db_item.item_type.value,
            "item_subtype": db_item.item_subtype,
            "item_code": db_item.item_code,
            "is_active": db_item.is_active,
            "created_at": db_item.created_at.isoformat(),
            "updated_at": db_item.updated_at.isoformat() if db_item.updated_at else None
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reporting effort item"
        )

@router.get("/by-effort/{reporting_effort_id}", response_model=List[ReportingEffortItemWithDetails])
async def read_items_by_reporting_effort(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
) -> List[ReportingEffortItemWithDetails]:
    """
    Get all items for a specific reporting effort.
    """
    try:
        # Verify reporting effort exists
        db_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )
        
        return await reporting_effort_item.get_by_reporting_effort(
            db, reporting_effort_id=reporting_effort_id
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reporting effort items"
        )

@router.put("/{item_id}", response_model=ReportingEffortItem)
async def update_reporting_effort_item(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    item_id: int,
    item_in: ReportingEffortItemUpdate,
) -> ReportingEffortItem:
    """
    Update an existing reporting effort item.
    """
    try:
        db_item = await reporting_effort_item.get(db, id=item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort item not found"
            )
        
        # Store original data for audit
        original_data = sqlalchemy_to_dict(db_item)
        
        updated_item = await reporting_effort_item.update(db, db_obj=db_item, obj_in=item_in)
        logger.info(f"Reporting effort item updated successfully: {updated_item.item_code} (ID: {updated_item.id})")
        
        # Log audit trail
        try:
            changes = {
                "before": original_data,
                "after": sqlalchemy_to_dict(updated_item)
            }
            await audit_log.log_action(
                db,
                table_name="reporting_effort_items",
                record_id=updated_item.id,
                action="UPDATE",
                user_id=getattr(request.state, 'user_id', None),
                changes=changes,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            logger.error(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket event
        try:
            await broadcast_reporting_effort_item_updated(updated_item)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return updated_item
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reporting effort item"
        )

@router.delete("/{item_id}", response_model=ReportingEffortItem)
async def delete_reporting_effort_item(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    item_id: int,
) -> ReportingEffortItem:
    """
    Delete a reporting effort item.
    Includes deletion protection based on programmer assignments.
    """
    try:
        db_item = await reporting_effort_item.get(db, id=item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort item not found"
            )
        
        # Check deletion protection
        protection_error = await reporting_effort_item.check_deletion_protection(db, id=item_id)
        if protection_error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=protection_error
            )
        
        # Store data for audit and broadcast
        item_data = sqlalchemy_to_dict(db_item)
        
        deleted_item = await reporting_effort_item.delete(db, id=item_id)
        logger.info(f"Reporting effort item deleted successfully: {deleted_item.item_code} (ID: {deleted_item.id})")
        
        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_items",
                record_id=deleted_item.id,
                action="DELETE",
                user_id=getattr(request.state, 'user_id', None),
                changes={"deleted": item_data},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            logger.error(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket event
        try:
            await broadcast_reporting_effort_item_deleted(deleted_item)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return deleted_item
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reporting effort item"
        )

# Bulk Upload Endpoints
@router.post("/{reporting_effort_id}/bulk-tlf", response_model=BulkUploadResponse)
async def bulk_create_tlf_items(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    items_in: List[BulkTLFItem],
    # Note: In production, add user role authentication here
    # current_user: User = Depends(get_current_admin_user)
) -> BulkUploadResponse:
    """
    Bulk create TLF items for a reporting effort.
    Admin only functionality.
    """
    errors = []
    created_items = []
    
    try:
        # Verify reporting effort exists
        db_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )
        
        # Validate all items first
        for idx, item in enumerate(items_in):
            # Validate subtype
            if item.item_subtype not in ['Table', 'Listing', 'Figure']:
                errors.append(f"Item {idx+1}: Invalid TLF type '{item.item_subtype}'. Must be Table, Listing, or Figure")
        
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
                # Create reporting effort item
                item_create = ReportingEffortItemCreate(
                    reporting_effort_id=reporting_effort_id,
                    source_type=SourceType.BULK_UPLOAD,
                    item_type=ItemType.TLF,
                    item_subtype=item.item_subtype,
                    item_code=item.item_code,
                    is_active=True
                )
                
                # Create TLF details if title provided
                tlf_details = None
                if item.title:
                    # In a real implementation, you'd create/get text elements here
                    # For now, just pass the data
                    tlf_details = {
                        "title": item.title
                    }
                
                created_item = await reporting_effort_item.create_with_details(
                    db,
                    obj_in=item_create,
                    tlf_details=tlf_details,
                    auto_create_tracker=True
                )
                
                # Convert to response model
                created_items.append(ReportingEffortItem.model_validate(created_item))
                
                # Broadcast WebSocket event
                try:
                    await broadcast_reporting_effort_item_created(created_item)
                except Exception:
                    pass  # Don't fail on broadcast error
                    
            except Exception as e:
                errors.append(f"Failed to create TLF '{item.item_code}': {str(e)}")
        
        # Log bulk upload audit trail
        if created_items:
            try:
                await audit_log.log_action(
                    db,
                    table_name="reporting_effort_items",
                    record_id=reporting_effort_id,  # Use effort ID for bulk operations
                    action="BULK_CREATE_TLF",
                    user_id=getattr(request.state, 'user_id', None),
                    changes={
                        "bulk_upload": {
                            "type": "TLF",
                            "created_count": len(created_items),
                            "errors": errors
                        }
                    },
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent")
                )
            except Exception as audit_error:
                logger.error(f"Audit logging error: {audit_error}")
        
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
            detail=f"Bulk TLF upload failed: {str(e)}"
        )

@router.post("/{reporting_effort_id}/bulk-dataset", response_model=BulkUploadResponse)
async def bulk_create_dataset_items(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    items_in: List[BulkDatasetItem],
    # Note: In production, add user role authentication here
    # current_user: User = Depends(get_current_admin_user)
) -> BulkUploadResponse:
    """
    Bulk create dataset items for a reporting effort.
    Admin only functionality.
    """
    errors = []
    created_items = []
    
    try:
        # Verify reporting effort exists
        db_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )
        
        # Validate all items first
        for idx, item in enumerate(items_in):
            # Validate subtype
            if item.item_subtype not in ['SDTM', 'ADaM']:
                errors.append(f"Item {idx+1}: Invalid dataset type '{item.item_subtype}'. Must be SDTM or ADaM")
        
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
                # Create reporting effort item
                item_create = ReportingEffortItemCreate(
                    reporting_effort_id=reporting_effort_id,
                    source_type=SourceType.BULK_UPLOAD,
                    item_type=ItemType.Dataset,
                    item_subtype=item.item_subtype,
                    item_code=item.item_code,
                    is_active=True
                )
                
                # Create dataset details
                dataset_details = None
                if item.label or item.acronyms:
                    dataset_details = {
                        "label": item.label,
                        "acronyms": item.acronyms
                    }
                
                created_item = await reporting_effort_item.create_with_details(
                    db,
                    obj_in=item_create,
                    dataset_details=dataset_details,
                    auto_create_tracker=True
                )
                
                # Convert to response model
                created_items.append(ReportingEffortItem.model_validate(created_item))
                
                # Broadcast WebSocket event
                try:
                    await broadcast_reporting_effort_item_created(created_item)
                except Exception:
                    pass  # Don't fail on broadcast error
                    
            except Exception as e:
                errors.append(f"Failed to create dataset '{item.item_code}': {str(e)}")
        
        # Log bulk upload audit trail
        if created_items:
            try:
                await audit_log.log_action(
                    db,
                    table_name="reporting_effort_items", 
                    record_id=reporting_effort_id,  # Use effort ID for bulk operations
                    action="BULK_CREATE_DATASET",
                    user_id=getattr(request.state, 'user_id', None),
                    changes={
                        "bulk_upload": {
                            "type": "Dataset",
                            "created_count": len(created_items),
                            "errors": errors
                        }
                    },
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent")
                )
            except Exception as audit_error:
                logger.error(f"Audit logging error: {audit_error}")
        
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
            detail=f"Bulk dataset upload failed: {str(e)}"
        )

# Copy Operations
@router.post("/{reporting_effort_id}/copy-from-package", response_model=List[ReportingEffortItemWithDetails])
async def copy_items_from_package(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    copy_request: CopyFromPackageRequest,
) -> List[ReportingEffortItemWithDetails]:
    """
    Copy items from a package to a reporting effort.
    """
    try:
        # Verify reporting effort exists
        db_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )
        
        # Verify package exists
        from app.crud.package import package
        db_package = await package.get(db, id=copy_request.package_id)
        if not db_package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source package not found"
            )
        
        created_items = await reporting_effort_item.copy_from_package(
            db,
            reporting_effort_id=reporting_effort_id,
            package_id=copy_request.package_id,
            item_ids=copy_request.item_ids
        )
        
        print(f"Copied {len(created_items)} items from package {copy_request.package_id} to reporting effort {reporting_effort_id}")
        
        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_items",
                record_id=reporting_effort_id,
                action="COPY_FROM_PACKAGE",
                user_id=getattr(request.state, 'user_id', None),
                changes={
                    "copy_operation": {
                        "source_package_id": copy_request.package_id,
                        "source_item_ids": copy_request.item_ids,
                        "copied_count": len(created_items),
                        "created_item_ids": [item.id for item in created_items]
                    }
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            logger.error(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket events for each created item
        for item in created_items:
            try:
                await broadcast_reporting_effort_item_created(item)
            except Exception:
                pass
        
        return created_items
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to copy items from package: {str(e)}"
        )

@router.post("/{reporting_effort_id}/copy-from-reporting-effort", response_model=List[ReportingEffortItemWithDetails])
async def copy_items_from_reporting_effort(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    copy_request: CopyFromReportingEffortRequest,
) -> List[ReportingEffortItemWithDetails]:
    """
    Copy items from another reporting effort.
    """
    try:
        # Verify target reporting effort exists
        db_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target reporting effort not found"
            )
        
        # Verify source reporting effort exists
        db_source_effort = await reporting_effort.get(db, id=copy_request.source_reporting_effort_id)
        if not db_source_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source reporting effort not found"
            )
        
        created_items = await reporting_effort_item.copy_from_reporting_effort(
            db,
            target_reporting_effort_id=reporting_effort_id,
            source_reporting_effort_id=copy_request.source_reporting_effort_id,
            item_ids=copy_request.item_ids
        )
        
        print(f"Copied {len(created_items)} items from reporting effort {copy_request.source_reporting_effort_id} to reporting effort {reporting_effort_id}")
        
        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_items",
                record_id=reporting_effort_id,
                action="COPY_FROM_REPORTING_EFFORT",
                user_id=getattr(request.state, 'user_id', None),
                changes={
                    "copy_operation": {
                        "source_reporting_effort_id": copy_request.source_reporting_effort_id,
                        "source_item_ids": copy_request.item_ids,
                        "copied_count": len(created_items),
                        "created_item_ids": [item.id for item in created_items]
                    }
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            logger.error(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket events for each created item
        for item in created_items:
            try:
                await broadcast_reporting_effort_item_created(item)
            except Exception:
                pass
        
        return created_items
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to copy items from reporting effort: {str(e)}"
        )