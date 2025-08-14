"""Reporting Effort Items API endpoints."""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.crud import reporting_effort_item, reporting_effort, audit_log, text_element
from app.crud.package_item import package_item
from app.db.session import get_db
from app.schemas.reporting_effort_item import (
    ReportingEffortItem, 
    ReportingEffortItemCreate, 
    ReportingEffortItemUpdate,
    ReportingEffortItemWithDetails,
    ReportingEffortItemCreateWithDetails,
    ReportingEffortTlfDetailsCreate,
    ReportingEffortDatasetDetailsCreate,
    CopyFromPackageRequest,
    CopyFromReportingEffortRequest
)
from app.schemas.text_element import TextElementCreate
from app.models.enums import ItemType, SourceType
from app.models.reporting_effort_item import ReportingEffortItem as ReportingEffortItemModel
from app.models.text_element import TextElementType
from app.models.user import UserRole
from app.utils import sqlalchemy_to_dict
from app.api.v1.websocket import manager

logger = logging.getLogger(__name__)

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
    ich_category: Optional[str] = Field(None, description="ICH category text")

class BulkDatasetItem(BaseModel):
    """Schema for bulk dataset upload."""
    item_subtype: str = Field(..., description="SDTM/ADaM")
    item_code: str = Field(..., description="Dataset name, e.g., DM")
    label: Optional[str] = Field(None, description="Dataset label")
    sorting_order: Optional[int] = Field(None, description="Display order")
    acronyms: Optional[str] = Field(None, description="Acronyms JSON string")

class BulkUploadResponse(BaseModel):
    """Response for bulk upload operations."""
    success: bool
    created_count: int
    errors: List[str] = Field(default_factory=list)
    items: List[dict] = Field(default_factory=list)

# CRUD Endpoints
@router.post("/", response_model=ReportingEffortItem, status_code=status.HTTP_201_CREATED)
async def create_reporting_effort_item(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    item_in: ReportingEffortItemCreate,
) -> ReportingEffortItem:
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
        
        # Check for duplicate item (moved to CRUD layer but also check here for better error message)
        existing_item = await reporting_effort_item.get_by_unique_key(
            db,
            reporting_effort_id=item_in.reporting_effort_id,
            item_type=item_in.item_type.value if hasattr(item_in.item_type, 'value') else item_in.item_type,
            item_subtype=item_in.item_subtype,
            item_code=item_in.item_code
        )
        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A {item_in.item_type} with code '{item_in.item_code}' already exists in this reporting effort"
            )
        
        created_item = await reporting_effort_item.create(
            db,
            obj_in=item_in
        )
        
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
        
        # Broadcast WebSocket event
        try:
            await broadcast_reporting_effort_item_created(created_item)
        except Exception as ws_error:
            logger.error(f"WebSocket broadcast error: {ws_error}")
        
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
            detail="Failed to create reporting effort item"
        )


@router.post("/{reporting_effort_id}/items", response_model=ReportingEffortItem, status_code=status.HTTP_201_CREATED)
async def create_reporting_effort_item_with_details(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    item_in: ReportingEffortItemCreateWithDetails,
) -> ReportingEffortItem:
    """
    Create a new reporting effort item with all details.
    """
    try:
        # Verify reporting effort exists
        db_effort = await reporting_effort.get(db, id=reporting_effort_id)
        if not db_effort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort not found"
            )
        
        # Check for duplicate item (moved to CRUD layer but also check here for better error message)
        existing_item = await reporting_effort_item.get_by_unique_key(
            db,
            reporting_effort_id=reporting_effort_id,
            item_type=item_in.item_type.value,
            item_subtype=item_in.item_subtype,
            item_code=item_in.item_code
        )
        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A {item_in.item_type.value} with code '{item_in.item_code}' already exists in this reporting effort"
            )
        
        # Ensure reporting_effort_id matches
        item_in.reporting_effort_id = reporting_effort_id
        
        created_item = await reporting_effort_item.create_with_details(
            db,
            obj_in=item_in,
            auto_create_tracker=True
        )
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
        
        # Broadcast WebSocket event
        try:
            await broadcast_reporting_effort_item_created(created_item)
        except Exception as ws_error:
            logger.error(f"WebSocket broadcast error: {ws_error}")
        
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
            detail="Failed to create reporting effort item"
        )


@router.get("/", response_model=dict)
async def read_reporting_effort_items(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> dict:
    """
    Retrieve reporting effort items with pagination.
    """
    try:
        items = await reporting_effort_item.get_multi(db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(items)} reporting effort items")
        
        # Convert to dict to avoid validation issues
        result = []
        for i, item in enumerate(items):
            try:
                # Convert enum to its value
                item_type_value = item.item_type.value if hasattr(item.item_type, 'value') else str(item.item_type)
                source_type_value = item.source_type.value if item.source_type and hasattr(item.source_type, 'value') else None
                
                item_dict = {
                    "id": item.id,
                    "reporting_effort_id": item.reporting_effort_id,
                    "source_type": source_type_value,
                    "source_id": item.source_id,
                    "source_item_id": item.source_item_id,
                    "item_type": item_type_value,
                    "item_subtype": item.item_subtype,
                    "item_code": item.item_code,
                    "is_active": item.is_active,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                }
                result.append(item_dict)
                logger.info(f"Successfully processed item {i+1}: {item.item_code}")
            except Exception as item_error:
                logger.error(f"Error processing item {i+1}: {str(item_error)}")
                logger.error(f"Item data: id={item.id}, item_type={item.item_type}, item_code={item.item_code}")
        
        return {"items": result, "count": len(result)}
    except Exception as e:
        logger.error(f"Error in read_reporting_effort_items: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve reporting effort items: {str(e)}"
        )

@router.get("/count")
async def get_items_count(
    *,
    db: AsyncSession = Depends(get_db)
):
    """Get count of reporting effort items."""
    try:
        from sqlalchemy import select, func
        result = await db.execute(select(func.count(ReportingEffortItemModel.id)))
        count = result.scalar()
        return {"count": count}
    except Exception as e:
        return {"error": str(e)}

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
            "source_type": db_item.source_type.value if db_item.source_type and hasattr(db_item.source_type, 'value') else None,
            "source_id": db_item.source_id,
            "source_item_id": db_item.source_item_id,
            "item_type": db_item.item_type.value if hasattr(db_item.item_type, 'value') else str(db_item.item_type),
            "item_subtype": db_item.item_subtype,
            "item_code": db_item.item_code,
            "is_active": db_item.is_active,
            "created_at": db_item.created_at.isoformat() if db_item.created_at else None,
            "updated_at": db_item.updated_at.isoformat() if db_item.updated_at else None
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reporting effort item"
        )

@router.get("/by-effort/{reporting_effort_id}")
async def read_items_by_reporting_effort(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
) -> List[dict]:
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
        
        items = await reporting_effort_item.get_by_reporting_effort(
            db, reporting_effort_id=reporting_effort_id
        )
        
        # Convert to dicts to avoid serialization issues
        result = []
        for item in items:
            item_dict = {
                "id": item.id,
                "reporting_effort_id": item.reporting_effort_id,
                "source_type": item.source_type.value if item.source_type and hasattr(item.source_type, 'value') else None,
                "source_id": item.source_id,
                "source_item_id": item.source_item_id,
                "item_type": item.item_type.value if hasattr(item.item_type, 'value') else str(item.item_type),
                "item_subtype": item.item_subtype,
                "item_code": item.item_code,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                "tlf_details": None,
                "dataset_details": None,
                "footnotes": [],
                "acronyms": [],
                "tracker": None
            }
            
            # Add TLF details if present
            if hasattr(item, 'tlf_details') and item.tlf_details:
                item_dict["tlf_details"] = {
                    "id": item.tlf_details.id,
                    "reporting_effort_item_id": item.tlf_details.reporting_effort_item_id,
                    "title_id": item.tlf_details.title_id,
                    "population_flag_id": item.tlf_details.population_flag_id,
                    "ich_category_id": item.tlf_details.ich_category_id
                }
            
            # Add dataset details if present
            if hasattr(item, 'dataset_details') and item.dataset_details:
                item_dict["dataset_details"] = {
                    "id": item.dataset_details.id,
                    "reporting_effort_item_id": item.dataset_details.reporting_effort_item_id,
                    "label": item.dataset_details.label,
                    "sorting_order": item.dataset_details.sorting_order,
                    "acronyms": item.dataset_details.acronyms
                }
            
            # Add footnotes if present
            if hasattr(item, 'footnotes') and item.footnotes:
                item_dict["footnotes"] = [
                    {
                        "footnote_id": f.footnote_id,
                        "sequence_number": f.sequence_number
                    }
                    for f in item.footnotes
                ]
            
            # Add acronyms if present
            if hasattr(item, 'acronyms') and item.acronyms:
                item_dict["acronyms"] = [
                    {"acronym_id": a.acronym_id}
                    for a in item.acronyms
                ]
            
            # Add tracker if present (safely)
            if hasattr(item, 'tracker') and item.tracker:
                try:
                    tracker = item.tracker
                    item_dict["tracker"] = {
                        "id": tracker.id,
                        "reporting_effort_item_id": tracker.reporting_effort_item_id,
                        "production_programmer_id": tracker.production_programmer_id,
                        "qc_programmer_id": tracker.qc_programmer_id,
                        "production_status": tracker.production_status.value if tracker.production_status and hasattr(tracker.production_status, 'value') else None,
                        "qc_status": tracker.qc_status.value if tracker.qc_status and hasattr(tracker.qc_status, 'value') else None,
                        "due_date": tracker.due_date.isoformat() if tracker.due_date else None,
                        "qc_completion_date": tracker.qc_completion_date.isoformat() if tracker.qc_completion_date else None,
                        "priority": tracker.priority.value if tracker.priority and hasattr(tracker.priority, 'value') else None,
                        "qc_level": tracker.qc_level.value if tracker.qc_level and hasattr(tracker.qc_level, 'value') else None,
                        "in_production_flag": tracker.in_production_flag,
                        "created_at": tracker.created_at.isoformat() if tracker.created_at else None,
                        "updated_at": tracker.updated_at.isoformat() if tracker.updated_at else None
                    }
                except Exception:
                    # Skip tracker if there's any issue accessing its attributes
                    pass
            
            result.append(item_dict)
            
        logger.info(f"Retrieved {len(result)} items for reporting effort {reporting_effort_id}")
        return result
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error retrieving items for reporting effort {reporting_effort_id}: {e}")
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
                
                # Create reporting effort item with details
                item_create = ReportingEffortItemCreateWithDetails(
                    reporting_effort_id=reporting_effort_id,
                    source_type=SourceType.BULK_UPLOAD.value,
                    item_type=ItemType.TLF.value,
                    item_subtype=item.item_subtype,
                    item_code=item.item_code,
                    is_active=True,
                    tlf_details=ReportingEffortTlfDetailsCreate(
                        title_id=title_id,
                        population_flag_id=population_flag_id,
                        ich_category_id=ich_category_id
                    ),
                    footnotes=[{"footnote_id": fid, "sequence_number": idx+1} 
                              for idx, fid in enumerate(footnote_ids)],
                    acronyms=[{"acronym_id": aid} for aid in acronym_ids]
                )
                
                created_item = await reporting_effort_item.create_with_details(
                    db,
                    obj_in=item_create,
                    auto_create_tracker=True
                )
                
                # Convert to dict for response
                created_items.append({
                    "id": created_item.id,
                    "reporting_effort_id": created_item.reporting_effort_id,
                    "source_type": created_item.source_type.value if created_item.source_type else None,
                    "source_id": created_item.source_id,
                    "source_item_id": created_item.source_item_id,
                    "item_type": created_item.item_type.value if hasattr(created_item.item_type, 'value') else str(created_item.item_type),
                    "item_subtype": created_item.item_subtype,
                    "item_code": created_item.item_code,
                    "is_active": created_item.is_active,
                    "created_at": created_item.created_at.isoformat() if created_item.created_at else None,
                    "updated_at": created_item.updated_at.isoformat() if created_item.updated_at else None
                })
                
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
                # Create reporting effort item with dataset details
                item_create = ReportingEffortItemCreateWithDetails(
                    reporting_effort_id=reporting_effort_id,
                    source_type=SourceType.BULK_UPLOAD.value,
                    item_type=ItemType.Dataset.value,
                    item_subtype=item.item_subtype,
                    item_code=item.item_code,
                    is_active=True,
                    dataset_details=ReportingEffortDatasetDetailsCreate(
                        label=item.label,
                        sorting_order=item.sorting_order,
                        acronyms=item.acronyms
                    ),
                    footnotes=[],
                    acronyms=[]
                )
                
                created_item = await reporting_effort_item.create_with_details(
                    db,
                    obj_in=item_create,
                    auto_create_tracker=True
                )
                
                # Convert to dict for response
                created_items.append({
                    "id": created_item.id,
                    "reporting_effort_id": created_item.reporting_effort_id,
                    "source_type": created_item.source_type.value if created_item.source_type else None,
                    "source_id": created_item.source_id,
                    "source_item_id": created_item.source_item_id,
                    "item_type": created_item.item_type.value if hasattr(created_item.item_type, 'value') else str(created_item.item_type),
                    "item_subtype": created_item.item_subtype,
                    "item_code": created_item.item_code,
                    "is_active": created_item.is_active,
                    "created_at": created_item.created_at.isoformat() if created_item.created_at else None,
                    "updated_at": created_item.updated_at.isoformat() if created_item.updated_at else None
                })
                
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
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting copy operation: package_id={copy_request.package_id}, reporting_effort_id={reporting_effort_id}")
        
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
        
        logger.info(f"Calling copy_from_package with validated inputs")
        created_items = await reporting_effort_item.copy_from_package(
            db,
            reporting_effort_id=reporting_effort_id,
            package_id=copy_request.package_id,
            item_ids=copy_request.item_ids
        )
        logger.info(f"Copy operation completed successfully, created {len(created_items)} items")
        
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
        
    except ValueError as e:
        # Handle validation errors (e.g., enum validation, duplicates)
        logger.error(f"Validation error during copy operation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        # Log the full exception for debugging
        logger.error(f"Unexpected error during copy operation: {str(e)}", exc_info=True)
        
        if isinstance(e, HTTPException):
            raise
        
        # Provide more specific error messages based on error type
        error_msg = str(e)
        if "enum" in error_msg.lower() or "sourcetype" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Database enum validation error: {error_msg}. This indicates an issue with data type conversion."
            )
        elif "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Duplicate item error: {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to copy items from package: {error_msg}"
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