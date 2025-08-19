"""Reporting Effort Item Tracker API endpoints."""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.crud import reporting_effort_item_tracker, reporting_effort_item, user, audit_log
from app.db.session import get_db

logger = logging.getLogger(__name__)
from app.schemas.reporting_effort_item_tracker import (
    ReportingEffortItemTracker,
    ReportingEffortItemTrackerCreate,
    ReportingEffortItemTrackerUpdate,
    ReportingEffortItemTrackerWithDetails
)
from app.models.reporting_effort_item_tracker import ProductionStatus, QCStatus
from app.models.user import UserRole
from app.utils import sqlalchemy_to_dict
from app.api.v1.websocket import (
    manager, 
    broadcast_reporting_effort_tracker_deleted,
    broadcast_reporting_effort_tracker_updated as broadcast_tracker_updated
)

async def broadcast_tracker_assignment_updated(tracker_data, assignment_type: str, programmer_id: Optional[int]):
    """Broadcast programmer assignment updates."""
    try:
        message_data = {
            "type": "tracker_assignment_updated",
            "data": {
                "tracker": sqlalchemy_to_dict(tracker_data),
                "assignment_type": assignment_type,  # "production" or "qc"
                "programmer_id": programmer_id
            }
        }
        await manager.broadcast(str(message_data).replace("'", '"'))
    except Exception as e:
        print(f"WebSocket broadcast error: {e}")

router = APIRouter()

# Request/Response Schemas
class AssignProgrammerRequest(BaseModel):
    """Schema for assigning a programmer to an item."""
    user_id: int = Field(..., description="ID of the programmer to assign")
    role: str = Field(..., description="Role type: 'production' or 'qc'")

class BulkAssignmentRequest(BaseModel):
    """Schema for bulk programmer assignments."""
    assignments: List[Dict[str, Any]] = Field(
        ..., 
        description="List of assignments with tracker_id, user_id, and role"
    )

class BulkStatusUpdateRequest(BaseModel):
    """Schema for bulk status updates."""
    updates: List[Dict[str, Any]] = Field(
        ...,
        description="List of updates with tracker_id and status fields"
    )

class WorkloadSummary(BaseModel):
    """Schema for workload summary response."""
    total_items: int
    in_progress: int
    completed: int
    by_programmer: List[Dict[str, Any]]

# CRUD Endpoints
@router.post("/", response_model=ReportingEffortItemTracker, status_code=status.HTTP_201_CREATED)
async def create_tracker(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    tracker_in: ReportingEffortItemTrackerCreate,
) -> ReportingEffortItemTracker:
    """
    Create a new tracker entry.
    Usually trackers are auto-created with items, but this allows manual creation.
    """
    try:
        # Verify item exists
        db_item = await reporting_effort_item.get(db, id=tracker_in.reporting_effort_item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort item not found"
            )
        
        # Check if tracker already exists
        existing_tracker = await reporting_effort_item_tracker.get_by_item(
            db, reporting_effort_item_id=tracker_in.reporting_effort_item_id
        )
        if existing_tracker:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tracker already exists for this item"
            )
        
        created_tracker = await reporting_effort_item_tracker.create(db, obj_in=tracker_in)
        print(f"Tracker created successfully for item {tracker_in.reporting_effort_item_id} (Tracker ID: {created_tracker.id})")
        
        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_item_tracker",
                record_id=created_tracker.id,
                action="CREATE",
                user_id=getattr(request.state, 'user_id', None),
                changes={"created": sqlalchemy_to_dict(created_tracker)},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket event
        try:
            await broadcast_tracker_updated(created_tracker)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return created_tracker
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tracker: {str(e)}"
        )

@router.get("/", response_model=List[ReportingEffortItemTracker])
async def read_trackers(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    production_status: Optional[ProductionStatus] = Query(None, description="Filter by production status"),
    qc_status: Optional[QCStatus] = Query(None, description="Filter by QC status"),
) -> List[ReportingEffortItemTracker]:
    """
    Retrieve trackers with optional filtering and pagination.
    """
    try:
        if production_status or qc_status:
            return await reporting_effort_item_tracker.get_by_status(
                db,
                production_status=production_status.value if production_status else None,
                qc_status=qc_status.value if qc_status else None
            )
        else:
            return await reporting_effort_item_tracker.get_multi(db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error retrieving trackers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve trackers: {str(e)}"
        )

@router.get("/{tracker_id}", response_model=ReportingEffortItemTracker)
async def read_tracker(
    *,
    db: AsyncSession = Depends(get_db),
    tracker_id: int,
) -> ReportingEffortItemTracker:
    """
    Get a specific tracker by ID.
    """
    try:
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )
        return db_tracker
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tracker"
        )

@router.get("/by-item/{item_id}", response_model=dict)
async def read_tracker_by_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
) -> dict:
    """
    Get tracker for a specific reporting effort item.
    """
    try:
        db_tracker = await reporting_effort_item_tracker.get_by_item(
            db, reporting_effort_item_id=item_id
        )
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found for this item"
            )
        # Return dict to avoid serialization issues
        return {
            "id": db_tracker.id,
            "reporting_effort_item_id": db_tracker.reporting_effort_item_id,
            "production_programmer_id": db_tracker.production_programmer_id,
            "qc_programmer_id": db_tracker.qc_programmer_id,
            "production_status": db_tracker.production_status,
            "qc_status": db_tracker.qc_status,
            "due_date": db_tracker.due_date.isoformat() if db_tracker.due_date else None,
            "qc_completion_date": db_tracker.qc_completion_date.isoformat() if db_tracker.qc_completion_date else None,
            "priority": db_tracker.priority,
            "qc_level": db_tracker.qc_level,
            "in_production_flag": db_tracker.in_production_flag,
            "created_at": db_tracker.created_at.isoformat(),
            "updated_at": db_tracker.updated_at.isoformat() if db_tracker.updated_at else None
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tracker"
        )

@router.get("/by-programmer/{programmer_id}", response_model=List[ReportingEffortItemTracker])
async def read_trackers_by_programmer(
    *,
    db: AsyncSession = Depends(get_db),
    programmer_id: int,
    role: str = Query("production", description="Role type: 'production' or 'qc'"),
) -> List[ReportingEffortItemTracker]:
    """
    Get all trackers assigned to a specific programmer.
    """
    try:
        # Verify user exists and has appropriate role
        db_user = await user.get(db, id=programmer_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programmer not found"
            )
        
        if role not in ["production", "qc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'production' or 'qc'"
            )
        
        return await reporting_effort_item_tracker.get_by_programmer(
            db, user_id=programmer_id, role=role
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve programmer assignments"
        )

@router.put("/{tracker_id}", response_model=ReportingEffortItemTracker)
async def update_tracker(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    tracker_id: int,
    tracker_in: ReportingEffortItemTrackerUpdate,
) -> ReportingEffortItemTracker:
    """
    Update a tracker entry.
    """
    try:
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )
        
        # Store original data for audit
        original_data = sqlalchemy_to_dict(db_tracker)
        
        updated_tracker = await reporting_effort_item_tracker.update(
            db, db_obj=db_tracker, obj_in=tracker_in
        )
        print(f"Tracker updated successfully: ID {updated_tracker.id}")
        
        # Log audit trail
        try:
            changes = {
                "before": original_data,
                "after": sqlalchemy_to_dict(updated_tracker)
            }
            await audit_log.log_action(
                db,
                table_name="reporting_effort_item_tracker",
                record_id=updated_tracker.id,
                action="UPDATE",
                user_id=getattr(request.state, 'user_id', None),
                changes=changes,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket event
        try:
            await broadcast_tracker_updated(updated_tracker)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return updated_tracker
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tracker"
        )

@router.delete("/{tracker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tracker(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    tracker_id: int,
) -> None:
    """
    Delete a tracker entry.
    """
    try:
        # Verify tracker exists
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )
        
        # Store tracker data for audit logging and broadcasting before deletion
        tracker_data = sqlalchemy_to_dict(db_tracker)
        
        # Get item details for enhanced WebSocket context
        item_info = None
        try:
            db_item = await reporting_effort_item.get(db, id=db_tracker.reporting_effort_item_id)
            if db_item:
                item_info = {
                    "item_code": db_item.item_code,
                    "item_type": db_item.item_type,
                    "effort_id": db_item.reporting_effort_id
                }
        except Exception as e:
            print(f"Error getting item info: {e}")
        
        # Get user context for enhanced WebSocket messaging
        user_info = None
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            try:
                db_user = await user.get(db, id=user_id)
                if db_user:
                    user_info = {
                        "user_id": db_user.id,
                        "username": db_user.username
                    }
            except Exception as e:
                print(f"Error getting user info: {e}")
        
        # Delete the tracker
        await reporting_effort_item_tracker.delete(db, id=tracker_id)
        print(f"Tracker deleted successfully: ID {tracker_id}")
        
        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_item_tracker",
                record_id=tracker_id,
                action="DELETE",
                user_id=user_id,
                changes={"deleted": tracker_data},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket event with enhanced context
        try:
            await broadcast_reporting_effort_tracker_deleted(
                tracker_data, 
                user_info=user_info, 
                item_info=item_info
            )
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        # Return 204 No Content (no response body)
        return
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tracker: {str(e)}"
        )

# Programmer Assignment Endpoints
@router.post("/{tracker_id}/assign-programmer", response_model=ReportingEffortItemTracker)
async def assign_programmer(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    tracker_id: int,
    assignment: AssignProgrammerRequest,
) -> ReportingEffortItemTracker:
    """
    Assign a programmer to a tracker for production or QC work.
    """
    try:
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )
        
        # Verify user exists and has appropriate role
        db_user = await user.get(db, id=assignment.user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check user role (in production, verify user can be assigned to this role)
        if assignment.role not in ["production", "qc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'production' or 'qc'"
            )
        
        # Store original data for audit
        original_data = sqlalchemy_to_dict(db_tracker)
        
        # Update the appropriate programmer field
        update_data = {}
        if assignment.role == "production":
            update_data["production_programmer_id"] = assignment.user_id
            # If assigning production programmer, reset status if needed
            if db_tracker.production_status == ProductionStatus.NOT_STARTED:
                update_data["production_status"] = ProductionStatus.IN_PROGRESS
        else:  # qc
            update_data["qc_programmer_id"] = assignment.user_id
            # QC can only start if production is completed
            if db_tracker.production_status == ProductionStatus.COMPLETED:
                if db_tracker.qc_status == QCStatus.NOT_STARTED:
                    update_data["qc_status"] = QCStatus.IN_PROGRESS
        
        # Apply the update
        tracker_update = ReportingEffortItemTrackerUpdate(**update_data)
        updated_tracker = await reporting_effort_item_tracker.update(
            db, db_obj=db_tracker, obj_in=tracker_update
        )
        
        print(f"Assigned {assignment.role} programmer {assignment.user_id} to tracker {tracker_id}")
        
        # Log audit trail
        try:
            changes = {
                "assignment": {
                    "role": assignment.role,
                    "programmer_id": assignment.user_id,
                    "programmer_username": db_user.username
                },
                "before": original_data,
                "after": sqlalchemy_to_dict(updated_tracker)
            }
            await audit_log.log_action(
                db,
                table_name="reporting_effort_item_tracker",
                record_id=updated_tracker.id,
                action="ASSIGN_PROGRAMMER",
                user_id=getattr(request.state, 'user_id', None),
                changes=changes,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        # Broadcast specialized assignment update
        try:
            await broadcast_tracker_assignment_updated(
                updated_tracker, assignment.role, assignment.user_id
            )
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return updated_tracker
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign programmer"
        )

@router.delete("/{tracker_id}/unassign-programmer", response_model=ReportingEffortItemTracker)
async def unassign_programmer(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    tracker_id: int,
    role: str = Query(..., description="Role to unassign: 'production' or 'qc'"),
) -> ReportingEffortItemTracker:
    """
    Unassign a programmer from a tracker.
    """
    try:
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )
        
        if role not in ["production", "qc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'production' or 'qc'"
            )
        
        # Store original data for audit
        original_data = sqlalchemy_to_dict(db_tracker)
        original_programmer_id = None
        
        # Update the appropriate programmer field
        update_data = {}
        if role == "production":
            original_programmer_id = db_tracker.production_programmer_id
            update_data["production_programmer_id"] = None
            # Reset status if in progress
            if db_tracker.production_status == ProductionStatus.IN_PROGRESS:
                update_data["production_status"] = ProductionStatus.NOT_STARTED
        else:  # qc
            original_programmer_id = db_tracker.qc_programmer_id
            update_data["qc_programmer_id"] = None
            # Reset QC status
            if db_tracker.qc_status in [QCStatus.IN_PROGRESS, QCStatus.FAILED]:
                update_data["qc_status"] = QCStatus.NOT_STARTED
        
        if not original_programmer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No {role} programmer currently assigned"
            )
        
        # Apply the update
        tracker_update = ReportingEffortItemTrackerUpdate(**update_data)
        updated_tracker = await reporting_effort_item_tracker.update(
            db, db_obj=db_tracker, obj_in=tracker_update
        )
        
        print(f"Unassigned {role} programmer from tracker {tracker_id}")
        
        # Log audit trail
        try:
            changes = {
                "unassignment": {
                    "role": role,
                    "previous_programmer_id": original_programmer_id
                },
                "before": original_data,
                "after": sqlalchemy_to_dict(updated_tracker)
            }
            await audit_log.log_action(
                db,
                table_name="reporting_effort_item_tracker",
                record_id=updated_tracker.id,
                action="UNASSIGN_PROGRAMMER",
                user_id=getattr(request.state, 'user_id', None),
                changes=changes,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        # Broadcast assignment update
        try:
            await broadcast_tracker_assignment_updated(updated_tracker, role, None)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return updated_tracker
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unassign programmer"
        )

# Bulk Operations
@router.post("/bulk-assign", response_model=List[ReportingEffortItemTracker])
async def bulk_assign_programmers(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    assignments: BulkAssignmentRequest,
    # Note: In production, add admin role authentication here
    # current_user: User = Depends(get_current_admin_user)
) -> List[ReportingEffortItemTracker]:
    """
    Bulk assign programmers to multiple trackers.
    Admin only functionality.
    """
    try:
        updated_trackers = []
        errors = []
        
        for assignment in assignments.assignments:
            try:
                tracker_id = assignment.get("tracker_id")
                user_id = assignment.get("user_id")
                role = assignment.get("role")
                
                if not all([tracker_id, user_id, role]):
                    errors.append(f"Missing required fields in assignment: {assignment}")
                    continue
                
                # Get tracker
                db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
                if not db_tracker:
                    errors.append(f"Tracker {tracker_id} not found")
                    continue
                
                # Verify user exists
                db_user = await user.get(db, id=user_id)
                if not db_user:
                    errors.append(f"User {user_id} not found")
                    continue
                
                # Update the appropriate programmer field
                update_data = {}
                if role == "production":
                    update_data["production_programmer_id"] = user_id
                elif role == "qc":
                    update_data["qc_programmer_id"] = user_id
                else:
                    errors.append(f"Invalid role '{role}' for tracker {tracker_id}")
                    continue
                
                # Apply the update
                tracker_update = ReportingEffortItemTrackerUpdate(**update_data)
                updated_tracker = await reporting_effort_item_tracker.update(
                    db, db_obj=db_tracker, obj_in=tracker_update
                )
                updated_trackers.append(updated_tracker)
                
                # Broadcast assignment update
                try:
                    await broadcast_tracker_assignment_updated(updated_tracker, role, user_id)
                except Exception:
                    pass
                
            except Exception as e:
                errors.append(f"Error processing assignment for tracker {assignment.get('tracker_id', 'unknown')}: {str(e)}")
        
        # Log bulk assignment audit trail
        if updated_trackers:
            try:
                await audit_log.log_action(
                    db,
                    table_name="reporting_effort_item_tracker",
                    record_id=0,  # Use 0 for bulk operations
                    action="BULK_ASSIGN_PROGRAMMERS",
                    user_id=getattr(request.state, 'user_id', None),
                    changes={
                        "bulk_assignment": {
                            "assigned_count": len(updated_trackers),
                            "errors": errors,
                            "assignments": assignments.assignments
                        }
                    },
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent")
                )
            except Exception as audit_error:
                print(f"Audit logging error: {audit_error}")
        
        if errors:
            print(f"Bulk assignment completed with {len(errors)} errors: {errors}")
        else:
            print(f"Bulk assignment completed successfully: {len(updated_trackers)} trackers updated")
        
        return updated_trackers
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk assignment failed: {str(e)}"
        )

@router.post("/bulk-status-update", response_model=List[ReportingEffortItemTracker])
async def bulk_update_status(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    updates: BulkStatusUpdateRequest,
) -> List[ReportingEffortItemTracker]:
    """
    Bulk update status for multiple trackers.
    """
    try:
        # Prepare updates for CRUD method
        crud_updates = []
        for update in updates.updates:
            if "id" not in update:
                if "tracker_id" in update:
                    update["id"] = update.pop("tracker_id")
                else:
                    continue  # Skip invalid updates
            crud_updates.append(update)
        
        updated_trackers = await reporting_effort_item_tracker.bulk_update(
            db, updates=crud_updates
        )
        
        print(f"Bulk status update completed: {len(updated_trackers)} trackers updated")
        
        # Log bulk update audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_item_tracker",
                record_id=0,  # Use 0 for bulk operations
                action="BULK_STATUS_UPDATE",
                user_id=getattr(request.state, 'user_id', None),
                changes={
                    "bulk_update": {
                        "updated_count": len(updated_trackers),
                        "updates": updates.updates
                    }
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        # Broadcast updates
        for tracker in updated_trackers:
            try:
                await broadcast_tracker_updated(tracker)
            except Exception:
                pass
        
        return updated_trackers
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk status update failed: {str(e)}"
        )

# Workload Management
@router.get("/workload-summary", response_model=WorkloadSummary)
async def get_workload_summary(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = Query(None, description="Filter by specific user ID"),
) -> WorkloadSummary:
    """
    Get workload summary for programmers.
    """
    try:
        summary_data = await reporting_effort_item_tracker.get_workload_summary(
            db, user_id=user_id
        )
        
        return WorkloadSummary(**summary_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workload summary: {str(e)}"
        )

@router.get("/workload/{programmer_id}", response_model=Dict[str, Any])
async def get_programmer_workload(
    *,
    db: AsyncSession = Depends(get_db),
    programmer_id: int,
) -> Dict[str, Any]:
    """
    Get detailed workload information for a specific programmer.
    """
    try:
        # Verify user exists
        db_user = await user.get(db, id=programmer_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programmer not found"
            )
        
        # Get production assignments
        production_trackers = await reporting_effort_item_tracker.get_by_programmer(
            db, user_id=programmer_id, role="production"
        )
        
        # Get QC assignments
        qc_trackers = await reporting_effort_item_tracker.get_by_programmer(
            db, user_id=programmer_id, role="qc"
        )
        
        # Calculate summary statistics
        production_stats = {
            "total": len(production_trackers),
            "not_started": len([t for t in production_trackers if t.production_status == "not_started"]),
            "in_progress": len([t for t in production_trackers if t.production_status == "in_progress"]),
            "completed": len([t for t in production_trackers if t.production_status == "completed"]),
            "on_hold": len([t for t in production_trackers if t.production_status == "on_hold"])
        }
        
        qc_stats = {
            "total": len(qc_trackers),
            "not_started": len([t for t in qc_trackers if t.qc_status == "not_started"]),
            "in_progress": len([t for t in qc_trackers if t.qc_status == "in_progress"]),
            "completed": len([t for t in qc_trackers if t.qc_status == "completed"]),
            "failed": len([t for t in qc_trackers if t.qc_status == "failed"])
        }
        
        return {
            "programmer_id": programmer_id,
            "programmer_username": db_user.username,
            "production": {
                "stats": production_stats,
                "trackers": [sqlalchemy_to_dict(t) for t in production_trackers]
            },
            "qc": {
                "stats": qc_stats,
                "trackers": [sqlalchemy_to_dict(t) for t in qc_trackers]
            },
            "total_workload": production_stats["total"] + qc_stats["total"]
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get programmer workload: {str(e)}"
        )

# Export/Import endpoints
@router.get("/export/{reporting_effort_id}")
async def export_trackers(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
    format: str = Query("json", enum=["json", "excel"])
) -> Any:
    """
    Export all trackers for a reporting effort.
    
    Formats:
    - json: JSON format for backup/import
    - excel: Excel format for manual editing
    """
    try:
        # Get all items for the reporting effort
        items = await reporting_effort_item.get_by_reporting_effort(
            db, reporting_effort_id=reporting_effort_id
        )
        
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No items found for this reporting effort"
            )
        
        # Get trackers for all items
        export_data = []
        for item in items:
            tracker = await reporting_effort_item_tracker.get_by_item(
                db, reporting_effort_item_id=item.id
            )
            
            if tracker:
                # Get user details
                prod_user = None
                qc_user = None
                if tracker.production_programmer_id:
                    prod_user = await user.get(db, id=tracker.production_programmer_id)
                if tracker.qc_programmer_id:
                    qc_user = await user.get(db, id=tracker.qc_programmer_id)
                
                export_data.append({
                    "item_id": item.id,
                    "item_type": item.item_type,
                    "item_subtype": item.item_subtype,
                    "item_code": item.item_code,
                    "tracker_id": tracker.id,
                    "production_programmer_username": prod_user.username if prod_user else None,
                    "production_status": tracker.production_status,
                    "qc_programmer_username": qc_user.username if qc_user else None,
                    "qc_status": tracker.qc_status,
                    "priority": tracker.priority,
                    "due_date": tracker.due_date.isoformat() if tracker.due_date else None,
                    "qc_completion_date": tracker.qc_completion_date.isoformat() if tracker.qc_completion_date else None,
                    "in_production_flag": tracker.in_production_flag
                })
        
        if format == "excel":
            # For Excel export, would need to implement Excel generation
            # For now, return JSON with a note
            return {
                "format": "excel_not_implemented",
                "note": "Excel export will be implemented in frontend",
                "data": export_data
            }
        
        return {
            "reporting_effort_id": reporting_effort_id,
            "export_date": datetime.utcnow().isoformat(),
            "total_items": len(export_data),
            "trackers": export_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export trackers: {str(e)}"
        )

class TrackerImportData(BaseModel):
    """Schema for importing tracker data."""
    item_code: str
    production_programmer_username: Optional[str] = None
    production_status: Optional[str] = None
    qc_programmer_username: Optional[str] = None
    qc_status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    qc_completion_date: Optional[date] = None

@router.post("/import/{reporting_effort_id}")
async def import_trackers(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    reporting_effort_id: int,
    trackers: List[TrackerImportData],
    update_existing: bool = Query(True, description="Update existing trackers or skip them")
) -> Dict[str, Any]:
    """
    Import/update trackers for a reporting effort.
    
    The import matches items by item_code and updates the tracker information.
    Usernames are resolved to user IDs.
    """
    try:
        # Get all items for the reporting effort
        items = await reporting_effort_item.get_by_reporting_effort(
            db, reporting_effort_id=reporting_effort_id
        )
        
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No items found for this reporting effort"
            )
        
        # Create item lookup by code
        item_by_code = {item.item_code: item for item in items}
        
        # Process imports
        updated = 0
        skipped = 0
        errors = []
        
        for import_data in trackers:
            # Find item by code
            if import_data.item_code not in item_by_code:
                errors.append(f"Item not found: {import_data.item_code}")
                continue
            
            item = item_by_code[import_data.item_code]
            
            # Get tracker for item
            tracker = await reporting_effort_item_tracker.get_by_item(
                db, reporting_effort_item_id=item.id
            )
            
            if not tracker:
                errors.append(f"No tracker for item: {import_data.item_code}")
                continue
            
            if not update_existing:
                skipped += 1
                continue
            
            # Prepare update data
            update_data = {}
            
            # Resolve usernames to IDs
            if import_data.production_programmer_username:
                prod_user = await user.get_by_username(
                    db, username=import_data.production_programmer_username
                )
                if prod_user:
                    update_data["production_programmer_id"] = prod_user.id
                else:
                    errors.append(f"User not found: {import_data.production_programmer_username}")
            
            if import_data.qc_programmer_username:
                qc_user = await user.get_by_username(
                    db, username=import_data.qc_programmer_username
                )
                if qc_user:
                    update_data["qc_programmer_id"] = qc_user.id
                else:
                    errors.append(f"User not found: {import_data.qc_programmer_username}")
            
            # Add other fields
            if import_data.production_status:
                update_data["production_status"] = import_data.production_status
            if import_data.qc_status:
                update_data["qc_status"] = import_data.qc_status
            if import_data.priority:
                update_data["priority"] = import_data.priority
            if import_data.due_date:
                update_data["due_date"] = import_data.due_date
            if import_data.qc_completion_date:
                update_data["qc_completion_date"] = import_data.qc_completion_date
            
            # Update tracker
            if update_data:
                await reporting_effort_item_tracker.update(
                    db, db_obj=tracker, obj_in=update_data
                )
                updated += 1
                
                # Broadcast update
                await broadcast_tracker_updated(tracker)
        
        # Log import to audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_item_tracker",
                record_id=reporting_effort_id,
                action="BULK_IMPORT",
                user_id=request.headers.get("X-User-Id"),
                changes_json=json.dumps({
                    "total_records": len(trackers),
                    "updated": updated,
                    "skipped": skipped,
                    "errors": len(errors)
                }),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        return {
            "message": "Import completed",
            "total_records": len(trackers),
            "updated": updated,
            "skipped": skipped,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import trackers: {str(e)}"
        )


@router.get("/bulk/{reporting_effort_id}", response_model=List[Dict[str, Any]])
async def get_trackers_bulk(
    *,
    db: AsyncSession = Depends(get_db),
    reporting_effort_id: int,
) -> List[Dict[str, Any]]:
    """
    Get all trackers for a reporting effort with optimized bulk loading.
    
    This endpoint replaces multiple individual API calls with a single
    optimized query that includes item details and programmer usernames.
    Designed to improve frontend performance by eliminating N+1 queries.
    """
    try:
        trackers = await reporting_effort_item_tracker.get_trackers_by_effort_bulk(
            db, reporting_effort_id=reporting_effort_id
        )
        
        logger.info(f"Retrieved {len(trackers)} trackers for effort {reporting_effort_id}")
        return trackers
        
    except Exception as e:
        logger.error(f"Error getting bulk trackers for effort {reporting_effort_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve trackers: {str(e)}"
        )