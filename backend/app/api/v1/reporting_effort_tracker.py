"""Reporting Effort Item Tracker API endpoints."""

from typing import List, Dict, Any, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.crud import reporting_effort_item_tracker, reporting_effort_item, user, audit_log
from app.db.session import get_db
from app.schemas.reporting_effort_item_tracker import (
    ReportingEffortItemTracker,
    ReportingEffortItemTrackerCreate,
    ReportingEffortItemTrackerUpdate,
    ReportingEffortItemTrackerWithDetails
)
from app.models.reporting_effort_item_tracker import ProductionStatus, QCStatus
from app.models.user import UserRole
from app.utils import sqlalchemy_to_dict
from app.api.v1.websocket import manager

# WebSocket broadcasting functions
async def broadcast_tracker_updated(tracker_data):
    """Broadcast that a tracker was updated."""
    try:
        message_data = {
            "type": "reporting_effort_tracker_updated",
            "data": sqlalchemy_to_dict(tracker_data)
        }
        await manager.broadcast(str(message_data).replace("'", '"'))
    except Exception as e:
        print(f"WebSocket broadcast error: {e}")

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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trackers"
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

@router.get("/by-item/{item_id}", response_model=ReportingEffortItemTracker)
async def read_tracker_by_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
) -> ReportingEffortItemTracker:
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
        return db_tracker
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