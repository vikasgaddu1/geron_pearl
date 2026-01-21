"""Reporting Effort Item Tracker API endpoints."""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.crud import reporting_effort_item_tracker, reporting_effort_item, reporting_effort, user, audit_log, app_settings, milestone_tracker_assignment
from app.db.session import get_db
from app.core.security import get_current_user
from app.core.study_permissions import (
    get_user_study_role,
    get_user_study_role_for_tracker,
    get_user_study_role_for_reporting_effort,
    is_study_admin,
    can_modify_in_study
)
from app.models.user_study_role import StudyRole

logger = logging.getLogger(__name__)
from app.schemas.reporting_effort_item_tracker import (
    ReportingEffortItemTracker,
    ReportingEffortItemTrackerCreate,
    ReportingEffortItemTrackerUpdate,
    ReportingEffortItemTrackerWithDetails
)
from app.models.reporting_effort_item_tracker import ProductionStatus, QCStatus
from app.models.user import User as UserModel
from app.models.tracker_status_history import TrackerStatusHistory
from app.services.tracker_workflow import TrackerWorkflowService
from app.utils import sqlalchemy_to_dict
from app.api.v1.websocket import (
    manager, 
    broadcast_reporting_effort_tracker_deleted,
    broadcast_reporting_effort_tracker_updated as broadcast_tracker_updated
)
from app.services.notification_service import create_assignment_notification

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
    except Exception:
        pass  # WebSocket broadcast is best-effort

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

class BulkAssignStatusRequest(BaseModel):
    """Unified schema for bulk assign and status update operations."""
    tracker_ids: List[int] = Field(..., description="List of tracker IDs to update")
    # Assignment fields (optional)
    production_programmer_id: Optional[int] = Field(None, description="Production programmer to assign")
    qc_programmer_id: Optional[int] = Field(None, description="QC programmer to assign")
    # Status fields (optional)
    production_status: Optional[str] = Field(None, description="New production status")
    qc_status: Optional[str] = Field(None, description="New QC status")
    # Due date (optional - auto-set to today+7 if not provided when assigning production programmer)
    due_date: Optional[date] = Field(None, description="Due date for the task")
    # Priority (optional)
    priority: Optional[str] = Field(None, description="Priority level (critical, high, medium, low)")
    
class BulkAssignStatusResponse(BaseModel):
    """Response for bulk assign/status operations."""
    updated: int = Field(..., description="Number of trackers updated")
    failed: int = Field(0, description="Number of failed updates")
    errors: List[str] = Field(default_factory=list, description="List of error messages")
    trackers: List[ReportingEffortItemTracker] = Field(default_factory=list, description="Updated trackers")

class WorkloadSummary(BaseModel):
    """Schema for workload summary response."""
    total_items: int
    in_progress: int
    completed: int
    by_programmer: List[Dict[str, Any]]

class CommentWithStatusRequest(BaseModel):
    """Schema for creating a comment with optional status update."""
    comment_text: str = Field(..., min_length=1, description="Comment content")
    production_status: Optional[str] = Field(None, description="New production status")
    qc_status: Optional[str] = Field(None, description="New QC status")

class StatusHistoryResponse(BaseModel):
    """Schema for status history entry response."""
    id: int
    status_field: str
    status_value: str
    entered_at: datetime
    exited_at: Optional[datetime]
    duration_seconds: Optional[float]
    changed_by_username: Optional[str]

# CRUD Endpoints
@router.post("/", response_model=ReportingEffortItemTracker, status_code=status.HTTP_201_CREATED)
async def create_tracker(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    tracker_in: ReportingEffortItemTrackerCreate,
    current_user: UserModel = Depends(get_current_user),
) -> ReportingEffortItemTracker:
    """
    Create a new tracker entry.
    Usually trackers are auto-created with items, but this allows manual creation.
    Requires LEAD access to the study.
    """
    try:
        # Verify item exists
        db_item = await reporting_effort_item.get(db, id=tracker_in.reporting_effort_item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort item not found"
            )

        # Authorization: require LEAD access to the study
        user_role = await get_user_study_role_for_tracker(db, current_user, None, db_item.id)
        if not is_study_admin(user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study leads can create trackers"
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
        
        # Validation: Production and QC programmer cannot be the same person
        if (tracker_in.production_programmer_id and tracker_in.qc_programmer_id and 
            tracker_in.production_programmer_id == tracker_in.qc_programmer_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Production and QC programmer cannot be the same person"
            )
        
        created_tracker = await reporting_effort_item_tracker.create(db, obj_in=tracker_in)

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
        except Exception:
            pass  # Audit logging is best-effort
        
        # Broadcast WebSocket event
        try:
            await broadcast_tracker_updated(created_tracker)
        except Exception:
            pass  # WebSocket broadcast is best-effort
        
        return created_tracker
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tracker: {str(e)}"
        )

@router.get("/", response_model=List[Dict[str, Any]])
async def read_trackers(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 1000,
    production_status: Optional[ProductionStatus] = Query(None, description="Filter by production status"),
    qc_status: Optional[QCStatus] = Query(None, description="Filter by QC status"),
    current_user: UserModel = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Retrieve trackers with optional filtering and pagination.
    Includes item details (item_code, item_subtype) for each tracker.
    """
    try:
        # Helper to serialize tracker with item details
        def serialize_tracker_with_item(tracker):
            data = sqlalchemy_to_dict(tracker)
            # Add item details if available
            if tracker.item:
                data["item_code"] = tracker.item.item_code
                data["item_subtype"] = tracker.item.item_subtype
                data["item_type"] = tracker.item.item_type.value if tracker.item.item_type else None
                
                # Consolidated item_title: TLF title > dataset label > item_description
                item_title = None
                if hasattr(tracker.item, 'tlf_details') and tracker.item.tlf_details:
                    if tracker.item.tlf_details.title:
                        # Use content if available, otherwise fall back to label
                        item_title = tracker.item.tlf_details.title.content or tracker.item.tlf_details.title.label
                if not item_title and hasattr(tracker.item, 'dataset_details') and tracker.item.dataset_details:
                    item_title = tracker.item.dataset_details.label
                if not item_title:
                    item_title = tracker.item.item_description
                data["item_title"] = item_title
                
                # Add study and reporting effort info for dashboards
                if tracker.item.reporting_effort:
                    re = tracker.item.reporting_effort
                    data["reporting_effort_id"] = re.id
                    data["reporting_effort_label"] = re.database_release_label
                    data["study_id"] = re.study_id
                    if re.study:
                        data["study_label"] = re.study.study_label
                    if re.database_release:
                        data["database_release_label"] = re.database_release.database_release_label
            return data
        
        if production_status or qc_status:
            trackers = await reporting_effort_item_tracker.get_by_status(
                db,
                production_status=production_status.value if production_status else None,
                qc_status=qc_status.value if qc_status else None
            )
        else:
            trackers = await reporting_effort_item_tracker.get_multi(db, skip=skip, limit=limit)
        
        return [serialize_tracker_with_item(t) for t in trackers]
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
    current_user: UserModel = Depends(get_current_user),
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
    current_user: UserModel = Depends(get_current_user),
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
    current_user: UserModel = Depends(get_current_user),
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
    current_user: UserModel = Depends(get_current_user),
) -> ReportingEffortItemTracker:
    """
    Update a tracker entry.
    
    Permissions:
    - Admin: Can update any field on any tracker
    - Study LEAD: Can update any field for trackers in their study
    - Study EDITOR: Can update fields for trackers they are assigned to (as production or QC programmer)
    - Study VIEWER: Cannot update trackers
    """
    try:
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )

        # Check if the reporting effort is locked
        db_item = await reporting_effort_item.get(db, id=db_tracker.reporting_effort_item_id)
        if db_item:
            db_effort = await reporting_effort.get(db, id=db_item.reporting_effort_id)
            if db_effort and db_effort.is_locked:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot update tracker: This reporting effort is locked. Reason: {db_effort.lock_reason}. Unlock to make changes."
                )

        # Convert to dict for validation
        update_data = tracker_in.model_dump(exclude_unset=True) if hasattr(tracker_in, 'model_dump') else tracker_in.dict(exclude_unset=True)
        
        # Check user's role and permissions
        is_admin = current_user.is_admin
        study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
        is_study_lead = is_study_admin(study_role)
        is_production_programmer = db_tracker.production_programmer_id == current_user.id
        is_qc_programmer = db_tracker.qc_programmer_id == current_user.id
        is_assigned = is_production_programmer or is_qc_programmer
        
        # General permission check: Must be admin, lead, or assigned (editor)
        # Viewers cannot update anything
        if not is_admin and not is_study_lead and not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this tracker. Only administrators, study leads, or assigned programmers can edit."
            )
        
        # For assigned editors (not admin/lead), restrict what they can change
        is_editor_only = not is_admin and not is_study_lead and is_assigned
        
        # Permission check for production_status: Only production programmer, admin, or study lead
        if 'production_status' in update_data and update_data['production_status']:
            if is_editor_only and not is_production_programmer:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the assigned production programmer, study lead, or admin can change production status"
                )
            # Validate: Cannot change production status without production programmer (except not_started)
            if update_data['production_status'] != 'not_started':
                new_prod_programmer = update_data.get('production_programmer_id', db_tracker.production_programmer_id)
                if not new_prod_programmer:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot update production status without a production programmer assigned"
                    )
            # Validate: Cannot set production status to 'completed' directly - it's auto-set by QC completion
            if update_data['production_status'] == 'completed':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Production status cannot be set to 'completed' directly. It is automatically set when QC marks the item as completed."
                )
        
        # Permission check for qc_status: Only QC programmer, admin, or study lead
        if 'qc_status' in update_data and update_data['qc_status']:
            if is_editor_only and not is_qc_programmer:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the assigned QC programmer, study lead, or admin can change QC status"
                )
            # Validate: Cannot change QC status without QC programmer (except not_started)
            if update_data['qc_status'] != 'not_started':
                new_qc_programmer = update_data.get('qc_programmer_id', db_tracker.qc_programmer_id)
                if not new_qc_programmer:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot update QC status without a QC programmer assigned"
                    )
            # Validate: QC can only be set to 'completed' or 'failed' when production is 'ready_for_qc'
            if update_data['qc_status'] in ['completed', 'failed']:
                if db_tracker.production_status != 'ready_for_qc':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"QC can only be marked as '{update_data['qc_status']}' when production status is 'Ready for QC'"
                    )
        
        # Permission check for programmer assignments: Only admin or lead can assign programmers
        if is_editor_only:
            if 'production_programmer_id' in update_data or 'qc_programmer_id' in update_data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only administrators or study leads can assign programmers to tasks"
                )
        
        # Validation: Production and QC programmer cannot be the same person
        new_prod_programmer = update_data.get('production_programmer_id', db_tracker.production_programmer_id)
        new_qc_programmer = update_data.get('qc_programmer_id', db_tracker.qc_programmer_id)
        if new_prod_programmer and new_qc_programmer and new_prod_programmer == new_qc_programmer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Production and QC programmer cannot be the same person"
            )
        
        # Auto-set due_date when assigning production programmer (if not already set)
        if 'production_programmer_id' in update_data and update_data['production_programmer_id']:
            if not db_tracker.due_date and 'due_date' not in update_data:
                due_date_offset = await app_settings.get_default_due_date_offset(db)
                update_data['due_date'] = date.today() + timedelta(days=due_date_offset)
        
        # Validation: Due date cannot be prior to today for incomplete tasks
        if 'due_date' in update_data and update_data['due_date']:
            new_due_date = update_data['due_date']
            # Check the effective statuses after this update
            effective_prod_status = update_data.get('production_status', db_tracker.production_status)
            effective_qc_status = update_data.get('qc_status', db_tracker.qc_status)
            is_task_completed = (effective_prod_status == 'completed' and effective_qc_status == 'completed')
            if not is_task_completed and new_due_date < date.today():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Due date cannot be prior to today for tasks that are not completed"
                )
        
        # Validation: Cannot set QC status to completed if there are unresolved comments
        if 'qc_status' in update_data and update_data['qc_status'] == 'completed':
            if db_tracker.unresolved_comment_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot mark QC as completed: {db_tracker.unresolved_comment_count} unresolved comment(s) must be addressed first"
                )
            # Auto-set qc_completion_date when QC status changes to completed
            update_data['qc_completion_date'] = date.today()
        
        # Apply auto-transitions for status changes using workflow service
        # This handles rules like: QC→FAILED triggers Production→IN_PROGRESS
        # Note: Auto-transitions should ALWAYS apply to enforce workflow rules,
        # even if the frontend sent the old status value (common in form submissions)
        if 'production_status' in update_data and update_data['production_status']:
            auto_updates = TrackerWorkflowService.apply_status_transition(
                db_tracker, "production_status", update_data['production_status']
            )
            # Auto-transitions override any explicit values to enforce workflow rules
            update_data.update(auto_updates)
        
        if 'qc_status' in update_data and update_data['qc_status']:
            auto_updates = TrackerWorkflowService.apply_status_transition(
                db_tracker, "qc_status", update_data['qc_status']
            )
            # Auto-transitions override any explicit values to enforce workflow rules
            update_data.update(auto_updates)
        
        # Store original data for audit and notification checks
        original_data = sqlalchemy_to_dict(db_tracker)
        original_prod_programmer_id = db_tracker.production_programmer_id
        original_qc_programmer_id = db_tracker.qc_programmer_id
        
        updated_tracker = await reporting_effort_item_tracker.update(
            db, db_obj=db_tracker, obj_in=update_data
        )

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
        except Exception:
            pass  # Audit logging is best-effort
        
        # Create notifications for new programmer assignments
        try:
            # Get item and study info for context
            item_code = None
            study_label = None
            if db_tracker.item:
                item_code = db_tracker.item.item_code
                if db_tracker.item.reporting_effort and db_tracker.item.reporting_effort.study:
                    study_label = db_tracker.item.reporting_effort.study.study_label
            
            # Notify production programmer if newly assigned (different from before)
            new_prod_id = update_data.get('production_programmer_id')
            if new_prod_id is not None and new_prod_id != original_prod_programmer_id and new_prod_id:
                await create_assignment_notification(
                    db,
                    assigned_user_id=new_prod_id,
                    assignment_type="production",
                    item_code=item_code or f"Tracker #{tracker_id}",
                    study_label=study_label,
                    tracker_id=tracker_id,
                    assigned_by_user_id=current_user.id,
                    assigned_by_username=current_user.username
                )
            
            # Notify QC programmer if newly assigned (different from before)
            new_qc_id = update_data.get('qc_programmer_id')
            if new_qc_id is not None and new_qc_id != original_qc_programmer_id and new_qc_id:
                await create_assignment_notification(
                    db,
                    assigned_user_id=new_qc_id,
                    assignment_type="qc",
                    item_code=item_code or f"Tracker #{tracker_id}",
                    study_label=study_label,
                    tracker_id=tracker_id,
                    assigned_by_user_id=current_user.id,
                    assigned_by_username=current_user.username
                )
        except Exception:
            pass  # Notification is best-effort

        # Broadcast WebSocket event
        try:
            await broadcast_tracker_updated(updated_tracker)
        except Exception:
            pass  # WebSocket broadcast is best-effort
        
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
    current_user: UserModel = Depends(get_current_user),
) -> None:
    """
    Delete a tracker entry.
    Admin or Study Lead only functionality.
    Cannot delete if tracker has associated comments.
    """
    # Permission check: Admin or Study Lead can delete trackers
    if not current_user.is_admin:
        study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
        if not is_study_admin(study_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators or study leads can delete trackers"
            )

    try:
        # Verify tracker exists
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )

        # Check for associated comments before deletion
        comments_count = await reporting_effort_item_tracker.get_comments_count(db, id=tracker_id)
        if comments_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete tracker: {comments_count} associated comment(s) exist. Delete them first."
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
        except Exception:
            pass
        
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
            except Exception:
                pass
        
        # Delete the tracker
        await reporting_effort_item_tracker.delete(db, id=tracker_id)

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
        except Exception:
            pass  # Audit logging is best-effort
        
        # Broadcast WebSocket event with enhanced context
        try:
            await broadcast_reporting_effort_tracker_deleted(
                tracker_data, 
                user_info=user_info, 
                item_info=item_info
            )
        except Exception:
            pass  # WebSocket broadcast is best-effort
        
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
    current_user: UserModel = Depends(get_current_user),
) -> ReportingEffortItemTracker:
    """
    Assign a programmer to a tracker for production or QC work.
    Admin only functionality.
    """
    # Permission check: Only admin or study lead can assign programmers
    if not current_user.is_admin:
        study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
        if not is_study_admin(study_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators or study leads can assign programmers to tasks"
            )
    
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
        
        # Note: Any user can be assigned to tasks - their study-scoped role 
        # determines what they can do (lead, editor, or viewer access)
        
        # Check assignment role is valid
        if assignment.role not in ["production", "qc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'production' or 'qc'"
            )
        
        # Validation: Production and QC programmer cannot be the same person
        if assignment.role == "production" and db_tracker.qc_programmer_id == assignment.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Production and QC programmer cannot be the same person"
            )
        if assignment.role == "qc" and db_tracker.production_programmer_id == assignment.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Production and QC programmer cannot be the same person"
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
        except Exception:
            pass  # Audit logging is best-effort
        
        # Create notification for the assigned user
        try:
            # Get item and study info for context
            item_code = None
            study_label = None
            if db_tracker.item:
                item_code = db_tracker.item.item_code
                if db_tracker.item.reporting_effort and db_tracker.item.reporting_effort.study:
                    study_label = db_tracker.item.reporting_effort.study.study_label
            
            await create_assignment_notification(
                db,
                assigned_user_id=assignment.user_id,
                assignment_type=assignment.role,
                item_code=item_code or f"Tracker #{tracker_id}",
                study_label=study_label,
                tracker_id=tracker_id,
                assigned_by_user_id=current_user.id,
                assigned_by_username=current_user.username
            )
        except Exception:
            pass  # Notification is best-effort

        # Broadcast specialized assignment update
        try:
            await broadcast_tracker_assignment_updated(
                updated_tracker, assignment.role, assignment.user_id
            )
        except Exception:
            pass  # WebSocket broadcast is best-effort
        
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
    current_user: UserModel = Depends(get_current_user),
) -> ReportingEffortItemTracker:
    """
    Unassign a programmer from a tracker.
    Admin only functionality.
    """
    # Permission check: Only admin or study lead can unassign programmers
    if not current_user.is_admin:
        study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
        if not is_study_admin(study_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators or study leads can unassign programmers"
            )

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
        except Exception:
            pass  # Audit logging is best-effort
        
        # Broadcast assignment update
        try:
            await broadcast_tracker_assignment_updated(updated_tracker, role, None)
        except Exception:
            pass  # WebSocket broadcast is best-effort
        
        return updated_tracker
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unassign programmer"
        )

# Helper function to check if a tracker's reporting effort is locked
async def check_tracker_effort_locked(db: AsyncSession, db_tracker) -> tuple[bool, str]:
    """Check if the reporting effort for a tracker is locked. Returns (is_locked, reason)."""
    db_item = await reporting_effort_item.get(db, id=db_tracker.reporting_effort_item_id)
    if db_item:
        db_effort = await reporting_effort.get(db, id=db_item.reporting_effort_id)
        if db_effort and db_effort.is_locked:
            return True, db_effort.lock_reason
    return False, ""


# Bulk Operations
@router.post("/bulk-assign", response_model=List[ReportingEffortItemTracker])
async def bulk_assign_programmers(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    assignments: BulkAssignmentRequest,
    current_user: UserModel = Depends(get_current_user),
) -> List[ReportingEffortItemTracker]:
    """
    Bulk assign programmers to multiple trackers.
    Admin or Study Lead only functionality.
    """
    # Global Admin can do anything
    is_global_admin = current_user.is_admin
    
    # For non-admins, verify study-level LEAD permissions for each tracker
    if not is_global_admin:
        for assignment in assignments.assignments:
            tracker_id = assignment.get("tracker_id")
            if tracker_id:
                study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
                if not is_study_admin(study_role):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You must be a study lead to perform bulk assignments on tracker {tracker_id}"
                    )
    
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
                
                # Check if the reporting effort is locked
                is_locked, lock_reason = await check_tracker_effort_locked(db, db_tracker)
                if is_locked:
                    errors.append(f"Tracker {tracker_id}: Cannot assign - reporting effort is locked. Reason: {lock_reason}")
                    continue
                
                # Verify user exists
                db_user = await user.get(db, id=user_id)
                if not db_user:
                    errors.append(f"User {user_id} not found")
                    continue
                
                # Note: Any user can be assigned - their study role determines access
                
                # Validation: Production and QC programmer cannot be the same person
                if role == "production" and db_tracker.qc_programmer_id == user_id:
                    errors.append(f"Tracker {tracker_id}: Production and QC programmer cannot be the same person")
                    continue
                if role == "qc" and db_tracker.production_programmer_id == user_id:
                    errors.append(f"Tracker {tracker_id}: Production and QC programmer cannot be the same person")
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
            except Exception:
                pass  # Audit logging is best-effort

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
    current_user: UserModel = Depends(get_current_user),
) -> List[ReportingEffortItemTracker]:
    """
    Bulk update status for multiple trackers.
    Only ADMIN or Study LEAD users can perform bulk status updates.
    Applies same validation rules as individual updates (unresolved comments, auto-transitions).
    """
    # Global Admin can do anything
    is_global_admin = current_user.is_admin
    
    # For non-admins, verify study-level LEAD permissions for each tracker
    if not is_global_admin:
        for update in updates.updates:
            tracker_id = update.get("id") or update.get("tracker_id")
            if tracker_id:
                study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
                if not is_study_admin(study_role):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You must be a study lead to perform bulk status updates on tracker {tracker_id}"
                    )

    updated_trackers = []
    errors = []

    try:
        for update in updates.updates:
            tracker_id = update.get("id") or update.get("tracker_id")
            if not tracker_id:
                continue

            try:
                # Get the tracker
                db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
                if not db_tracker:
                    errors.append(f"Tracker {tracker_id} not found")
                    continue

                # Check if the reporting effort is locked
                is_locked, lock_reason = await check_tracker_effort_locked(db, db_tracker)
                if is_locked:
                    errors.append(f"Tracker {tracker_id}: Cannot update - reporting effort is locked. Reason: {lock_reason}")
                    continue

                update_data = {k: v for k, v in update.items() if k not in ["id", "tracker_id"]}

                # Validation: Production and QC programmer cannot be the same person
                new_prod_programmer = update_data.get("production_programmer_id", db_tracker.production_programmer_id)
                new_qc_programmer = update_data.get("qc_programmer_id", db_tracker.qc_programmer_id)
                if new_prod_programmer and new_qc_programmer and new_prod_programmer == new_qc_programmer:
                    errors.append(f"Tracker {tracker_id}: Production and QC programmer cannot be the same person")
                    continue

                # Validation: Due date cannot be prior to today for incomplete tasks
                new_due_date = update_data.get("due_date")
                if new_due_date:
                    effective_prod_status = update_data.get("production_status", db_tracker.production_status)
                    effective_qc_status = update_data.get("qc_status", db_tracker.qc_status)
                    is_task_completed = (effective_prod_status == 'completed' and effective_qc_status == 'completed')
                    if not is_task_completed and new_due_date < date.today():
                        errors.append(f"Tracker {tracker_id}: Due date cannot be prior to today for tasks that are not completed")
                        continue

                # Validate: Cannot set QC status to completed if there are unresolved comments
                if update_data.get("qc_status") == "completed":
                    if db_tracker.unresolved_comment_count > 0:
                        errors.append(f"Tracker {tracker_id}: Cannot mark QC as completed - {db_tracker.unresolved_comment_count} unresolved comment(s)")
                        continue
                    # Auto-set qc_completion_date
                    update_data["qc_completion_date"] = date.today()

                # Apply auto-transitions for status changes using workflow service
                if update_data.get("production_status"):
                    auto_updates = TrackerWorkflowService.apply_status_transition(
                        db_tracker, "production_status", update_data["production_status"]
                    )
                    update_data.update(auto_updates)

                if update_data.get("qc_status"):
                    auto_updates = TrackerWorkflowService.apply_status_transition(
                        db_tracker, "qc_status", update_data["qc_status"]
                    )
                    update_data.update(auto_updates)

                # Apply the update
                updated_tracker = await reporting_effort_item_tracker.update(
                    db, db_obj=db_tracker, obj_in=update_data
                )
                updated_trackers.append(updated_tracker)

                # Broadcast update
                try:
                    await broadcast_tracker_updated(updated_tracker)
                except Exception:
                    pass

            except Exception as e:
                errors.append(f"Tracker {tracker_id}: {str(e)}")

        # Log bulk update audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_item_tracker",
                record_id=0,  # Use 0 for bulk operations
                action="BULK_STATUS_UPDATE",
                user_id=current_user.id,
                changes={
                    "bulk_update": {
                        "updated_count": len(updated_trackers),
                        "error_count": len(errors),
                        "updates": updates.updates,
                        "errors": errors
                    }
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort

        return updated_trackers

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk status update failed: {str(e)}"
        )


@router.post("/bulk-assign-status", response_model=BulkAssignStatusResponse)
async def bulk_assign_and_update_status(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    data: BulkAssignStatusRequest,
    current_user: UserModel = Depends(get_current_user),
) -> BulkAssignStatusResponse:
    """
    Unified endpoint to bulk assign programmers and update statuses.
    Validates that status cannot be changed without an assigned programmer.
    Only ADMIN or Study LEAD users can perform bulk operations.
    """
    # Global Admin can do anything
    is_global_admin = current_user.is_admin
    
    # For non-admins, verify study-level LEAD permissions for each tracker
    if not is_global_admin:
        for tracker_id in data.tracker_ids:
            study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
            if not is_study_admin(study_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You must be a study lead to perform bulk operations on tracker {tracker_id}"
                )
    
    updated_trackers = []
    errors = []
    
    # Validate at least one action is specified
    has_assignment = data.production_programmer_id is not None or data.qc_programmer_id is not None
    has_status_update = data.production_status is not None or data.qc_status is not None
    
    if not has_assignment and not has_status_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one assignment or status update must be specified"
        )
    
    for tracker_id in data.tracker_ids:
        try:
            # Get the tracker
            db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
            if not db_tracker:
                errors.append(f"Tracker {tracker_id} not found")
                continue
            
            # Check if the reporting effort is locked
            is_locked, lock_reason = await check_tracker_effort_locked(db, db_tracker)
            if is_locked:
                errors.append(f"Tracker {tracker_id}: Cannot modify - reporting effort is locked. Reason: {lock_reason}")
                continue
            
            # Store original programmer IDs for notification comparison
            original_prod_programmer_id = db_tracker.production_programmer_id
            original_qc_programmer_id = db_tracker.qc_programmer_id
            
            update_data = {}
            
            # Note: Any user can be assigned - their study role determines access
            
            # Handle assignments first
            if data.production_programmer_id is not None:
                update_data["production_programmer_id"] = data.production_programmer_id
                # Auto-set due_date using configurable offset if not already set and not provided
                if not db_tracker.due_date and data.due_date is None:
                    due_date_offset = await app_settings.get_default_due_date_offset(db)
                    update_data["due_date"] = date.today() + timedelta(days=due_date_offset)
                elif data.due_date is not None:
                    update_data["due_date"] = data.due_date
                    
            if data.qc_programmer_id is not None:
                update_data["qc_programmer_id"] = data.qc_programmer_id
            
            # Validation: Production and QC programmer cannot be the same person
            new_prod_programmer = update_data.get("production_programmer_id", db_tracker.production_programmer_id)
            new_qc_programmer = update_data.get("qc_programmer_id", db_tracker.qc_programmer_id)
            if new_prod_programmer and new_qc_programmer and new_prod_programmer == new_qc_programmer:
                errors.append(f"Tracker {tracker_id}: Production and QC programmer cannot be the same person")
                continue
            
            # Validation: Due date cannot be prior to today for incomplete tasks
            new_due_date = update_data.get("due_date")
            if new_due_date:
                effective_prod_status = data.production_status if data.production_status else db_tracker.production_status
                effective_qc_status = data.qc_status if data.qc_status else db_tracker.qc_status
                is_task_completed = (effective_prod_status == 'completed' and effective_qc_status == 'completed')
                if not is_task_completed and new_due_date < date.today():
                    errors.append(f"Tracker {tracker_id}: Due date cannot be prior to today for tasks that are not completed")
                    continue
            
            # Validate status updates - programmer must be assigned (except for not_started)
            if data.production_status is not None:
                # Allow not_started without programmer (it's the reset/initial state)
                if data.production_status != 'not_started':
                    prod_programmer_id = update_data.get("production_programmer_id", db_tracker.production_programmer_id)
                    if not prod_programmer_id:
                        errors.append(f"Tracker {tracker_id}: Cannot update production status without assigning a production programmer")
                        continue
                update_data["production_status"] = data.production_status
                
            if data.qc_status is not None:
                # Allow not_started without programmer (it's the reset/initial state)
                if data.qc_status != 'not_started':
                    qc_programmer_id = update_data.get("qc_programmer_id", db_tracker.qc_programmer_id)
                    if not qc_programmer_id:
                        errors.append(f"Tracker {tracker_id}: Cannot update QC status without assigning a QC programmer")
                        continue
                # Validate: Cannot mark QC as completed if there are unresolved comments
                if data.qc_status == 'completed':
                    if db_tracker.unresolved_comment_count > 0:
                        errors.append(f"Tracker {tracker_id}: Cannot mark QC as completed - {db_tracker.unresolved_comment_count} unresolved comment(s)")
                        continue
                    update_data["qc_completion_date"] = date.today()
                update_data["qc_status"] = data.qc_status

            # Apply auto-transitions for status changes using workflow service
            if update_data.get("production_status"):
                auto_updates = TrackerWorkflowService.apply_status_transition(
                    db_tracker, "production_status", update_data["production_status"]
                )
                update_data.update(auto_updates)

            if update_data.get("qc_status"):
                auto_updates = TrackerWorkflowService.apply_status_transition(
                    db_tracker, "qc_status", update_data["qc_status"]
                )
                update_data.update(auto_updates)

            # Handle priority
            if data.priority is not None:
                update_data["priority"] = data.priority
            
            # Apply the update if there's data
            if update_data:
                updated_tracker = await reporting_effort_item_tracker.update(
                    db, db_obj=db_tracker, obj_in=update_data
                )
                updated_trackers.append(updated_tracker)
                
                # Broadcast update
                try:
                    await broadcast_tracker_updated(updated_tracker)
                except Exception:
                    pass
                
                # Create notifications for new assignments
                try:
                    # Get item and study info for context
                    item_code = None
                    study_label = None
                    if db_tracker.item:
                        item_code = db_tracker.item.item_code
                        if db_tracker.item.reporting_effort and db_tracker.item.reporting_effort.study:
                            study_label = db_tracker.item.reporting_effort.study.study_label
                    
                    # Notify production programmer if newly assigned (different from original)
                    if data.production_programmer_id is not None and data.production_programmer_id != original_prod_programmer_id and data.production_programmer_id:
                        await create_assignment_notification(
                            db,
                            assigned_user_id=data.production_programmer_id,
                            assignment_type="production",
                            item_code=item_code or f"Tracker #{tracker_id}",
                            study_label=study_label,
                            tracker_id=tracker_id,
                            assigned_by_user_id=current_user.id,
                            assigned_by_username=current_user.username
                        )
                    
                    # Notify QC programmer if newly assigned (different from original)
                    if data.qc_programmer_id is not None and data.qc_programmer_id != original_qc_programmer_id and data.qc_programmer_id:
                        await create_assignment_notification(
                            db,
                            assigned_user_id=data.qc_programmer_id,
                            assignment_type="qc",
                            item_code=item_code or f"Tracker #{tracker_id}",
                            study_label=study_label,
                            tracker_id=tracker_id,
                            assigned_by_user_id=current_user.id,
                            assigned_by_username=current_user.username
                        )
                except Exception:
                    pass  # Notification is best-effort
                    
        except Exception as e:
            errors.append(f"Tracker {tracker_id}: {str(e)}")
    
    # Log audit trail
    try:
        await audit_log.log_action(
            db,
            table_name="reporting_effort_item_tracker",
            record_id=0,
            action="BULK_ASSIGN_STATUS",
            user_id=current_user.id,
            changes={
                "tracker_ids": data.tracker_ids,
                "production_programmer_id": data.production_programmer_id,
                "qc_programmer_id": data.qc_programmer_id,
                "production_status": data.production_status,
                "qc_status": data.qc_status,
                "updated_count": len(updated_trackers),
                "errors": errors
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass  # Audit logging is best-effort

    # Convert trackers to dict for response
    tracker_dicts = []
    for t in updated_trackers:
        tracker_dict = sqlalchemy_to_dict(t)
        tracker_dicts.append(ReportingEffortItemTracker(**tracker_dict))
    
    return BulkAssignStatusResponse(
        updated=len(updated_trackers),
        failed=len(errors),
        errors=errors,
        trackers=tracker_dicts
    )


# Workload Management
@router.get("/workload-summary", response_model=WorkloadSummary)
async def get_workload_summary(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: Optional[int] = Query(None, description="Filter by specific user ID"),
    current_user: UserModel = Depends(get_current_user),
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
    current_user: UserModel = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get detailed workload information for a specific programmer.
    Includes item details (item_code) and full hierarchy (study, db release, reporting effort).
    """
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker as TrackerModel
    from app.models.reporting_effort_item import ReportingEffortItem
    from app.models.reporting_effort import ReportingEffort

    try:
        # Verify user exists
        db_user = await user.get(db, id=programmer_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Programmer not found"
            )

        # Query production assignments with full hierarchy eager loading using joinedload
        prod_result = await db.execute(
            select(TrackerModel)
            .options(
                joinedload(TrackerModel.item)
                .joinedload(ReportingEffortItem.reporting_effort)
                .joinedload(ReportingEffort.database_release),
                joinedload(TrackerModel.item)
                .joinedload(ReportingEffortItem.reporting_effort)
                .joinedload(ReportingEffort.study)
            )
            .where(TrackerModel.production_programmer_id == programmer_id)
            .order_by(TrackerModel.priority, TrackerModel.due_date)
        )
        production_trackers = list(prod_result.unique().scalars().all())

        # Query QC assignments with full hierarchy eager loading using joinedload
        qc_result = await db.execute(
            select(TrackerModel)
            .options(
                joinedload(TrackerModel.item)
                .joinedload(ReportingEffortItem.reporting_effort)
                .joinedload(ReportingEffort.database_release),
                joinedload(TrackerModel.item)
                .joinedload(ReportingEffortItem.reporting_effort)
                .joinedload(ReportingEffort.study)
            )
            .where(TrackerModel.qc_programmer_id == programmer_id)
            .order_by(TrackerModel.priority, TrackerModel.due_date)
        )
        qc_trackers = list(qc_result.unique().scalars().all())

        logger.info(f"Workload query: Found {len(production_trackers)} production trackers, {len(qc_trackers)} QC trackers")

        # Helper to serialize tracker with item details and full hierarchy
        # Uses tracker.item which was already loaded via joinedload
        def serialize_tracker_with_item(tracker):
            data = sqlalchemy_to_dict(tracker)
            
            # Use the item relationship already loaded via joinedload
            item = tracker.item
            
            # Add item details if available
            if item:
                data["item_code"] = item.item_code
                data["item_subtype"] = item.item_subtype  # table/listing/figure or SDTM/ADaM
                data["item_type"] = item.item_type.value if item.item_type else None
                logger.debug(f"DEBUG: Tracker {tracker.id} -> item_code={item.item_code}")

                # Add reporting effort hierarchy
                if item.reporting_effort:
                    re = item.reporting_effort
                    data["reporting_effort_id"] = re.id
                    data["reporting_effort_label"] = re.database_release_label
                    logger.debug(f"DEBUG: Tracker {tracker.id} -> RE label={re.database_release_label}")

                    # Add database release info
                    if re.database_release:
                        data["database_release_label"] = re.database_release.database_release_label
                        data["database_release_id"] = re.database_release.id
                        logger.debug(f"DEBUG: Tracker {tracker.id} -> DB label={re.database_release.database_release_label}")

                    # Add study info
                    if re.study:
                        data["study_label"] = re.study.study_label
                        data["study_id"] = re.study.id
                        logger.debug(f"DEBUG: Tracker {tracker.id} -> Study label={re.study.study_label}")
                else:
                    logger.warning(f"DEBUG: Tracker {tracker.id} item has no reporting_effort relationship")
            else:
                logger.warning(f"DEBUG: Tracker {tracker.id} has no item relationship loaded")
            
            return data
        
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
                "trackers": [serialize_tracker_with_item(t) for t in production_trackers]
            },
            "qc": {
                "stats": qc_stats,
                "trackers": [serialize_tracker_with_item(t) for t in qc_trackers]
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
    format: str = Query("json", enum=["json", "excel"]),
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Export all trackers for a reporting effort.
    Requires authentication and LEAD access to the study.

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

        # Authorization: check user has access to this study via the first item
        user_role = await get_user_study_role_for_reporting_effort(db, current_user, reporting_effort_id)
        if not is_study_admin(user_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only study leads can export trackers"
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
    update_existing: bool = Query(True, description="Update existing trackers or skip them"),
    current_user: UserModel = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Import/update trackers for a reporting effort.
    Admin only functionality.

    The import matches items by item_code and updates the tracker information.
    Usernames are resolved to user IDs.
    """
    # Permission check: Only admin can perform bulk imports
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform bulk imports"
        )

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
            
            # Validation: Production and QC programmer cannot be the same person
            new_prod_programmer = update_data.get("production_programmer_id", tracker.production_programmer_id)
            new_qc_programmer = update_data.get("qc_programmer_id", tracker.qc_programmer_id)
            if new_prod_programmer and new_qc_programmer and new_prod_programmer == new_qc_programmer:
                errors.append(f"Item {import_data.item_code}: Production and QC programmer cannot be the same person")
                continue
            
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
            
            # Validation: Due date cannot be prior to today for incomplete tasks
            new_due_date = update_data.get("due_date")
            if new_due_date:
                effective_prod_status = update_data.get("production_status", tracker.production_status)
                effective_qc_status = update_data.get("qc_status", tracker.qc_status)
                is_task_completed = (effective_prod_status == 'completed' and effective_qc_status == 'completed')
                if not is_task_completed and new_due_date < date.today():
                    errors.append(f"Item {import_data.item_code}: Due date cannot be prior to today for tasks that are not completed")
                    continue
            
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
                user_id=current_user.id,
                changes={
                    "total_records": len(trackers),
                    "updated": updated,
                    "skipped": skipped,
                    "errors": len(errors)
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception:
            pass  # Audit logging is best-effort
        
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
    current_user: UserModel = Depends(get_current_user),
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


# ========================================================================
# PHASE 3: Workflow Endpoints with Validation and Permissions
# ========================================================================

@router.post("/{tracker_id}/comment-with-status", response_model=Dict[str, Any])
async def create_comment_with_status(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    tracker_id: int,
    data: CommentWithStatusRequest,
) -> Dict[str, Any]:
    """
    Create a comment with optional status update.
    
    This is the primary endpoint for the unified comment/status workflow.
    It atomically creates a comment and updates status (if provided).
    
    Validation:
    - Status changes require programmer assignment
    - Production cannot be set to COMPLETED directly
    - QC FAILED/COMPLETED requires Production to be READY_FOR_QC
    
    Permissions:
    - Admin: Can change any status
    - Study Lead: Can change any status within their study
    - Editor: Can only change status for tasks they're assigned to
    - Viewer: Cannot change status
    """
    from app.crud import tracker_comment
    from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker as TrackerModel
    
    try:
        # Get tracker
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )
        
        # Get user's study role for this tracker
        study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
        
        # Store original statuses for history tracking
        original_prod_status = db_tracker.production_status
        original_qc_status = db_tracker.qc_status
        
        # Process status updates if provided
        status_updates = {}
        
        if data.production_status:
            # Check permission (pass study_role for Study Lead access)
            has_permission, perm_error = TrackerWorkflowService.check_status_change_permission(
                current_user, db_tracker, "production_status", study_role
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=perm_error
                )
            
            # Validate transition
            is_valid, val_error = TrackerWorkflowService.validate_status_change(
                db_tracker, "production_status", data.production_status
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=val_error
                )
            
            # Get all updates including auto-transitions
            status_updates.update(
                TrackerWorkflowService.apply_status_transition(
                    db_tracker, "production_status", data.production_status
                )
            )
        
        if data.qc_status:
            # Check permission (pass study_role for Study Lead access)
            has_permission, perm_error = TrackerWorkflowService.check_status_change_permission(
                current_user, db_tracker, "qc_status", study_role
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=perm_error
                )
            
            # Validate transition
            is_valid, val_error = TrackerWorkflowService.validate_status_change(
                db_tracker, "qc_status", data.qc_status
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=val_error
                )
            
            # Validation: Cannot set QC status to completed if there are unresolved comments
            if data.qc_status == 'completed' and db_tracker.unresolved_comment_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot mark QC as completed: {db_tracker.unresolved_comment_count} unresolved comment(s) must be addressed first"
                )
            
            # Get all updates including auto-transitions
            status_updates.update(
                TrackerWorkflowService.apply_status_transition(
                    db_tracker, "qc_status", data.qc_status
                )
            )
        
        # Apply status updates if any
        if status_updates:
            for field, value in status_updates.items():
                setattr(db_tracker, field, value)
            db_tracker.updated_at = datetime.utcnow()
            db.add(db_tracker)
            
            # Create history entries
            history_entries = TrackerWorkflowService.create_history_entries(
                tracker_id=tracker_id,
                updates=status_updates,
                previous_production_status=original_prod_status,
                previous_qc_status=original_qc_status,
                user_id=current_user.id
            )
            
            # Close out previous history entries
            if history_entries:
                from sqlalchemy import select, and_
                now = datetime.utcnow()
                
                for entry in history_entries:
                    # Find the previous open entry for this field and close it
                    prev_result = await db.execute(
                        select(TrackerStatusHistory)
                        .where(and_(
                            TrackerStatusHistory.tracker_id == tracker_id,
                            TrackerStatusHistory.status_field == entry.status_field,
                            TrackerStatusHistory.exited_at.is_(None)
                        ))
                    )
                    prev_entry = prev_result.scalar_one_or_none()
                    if prev_entry:
                        prev_entry.exited_at = now
                        db.add(prev_entry)
                    
                    # Add the new entry
                    db.add(entry)
        
        # Create the comment
        from app.schemas.tracker_comment import TrackerCommentCreate
        comment_data = TrackerCommentCreate(
            tracker_id=tracker_id,
            comment_text=data.comment_text,
            comment_type="programming",
            parent_comment_id=None
        )
        new_comment = await tracker_comment.create(
            db,
            obj_in=comment_data,
            user_id=current_user.id
        )
        
        await db.commit()
        await db.refresh(db_tracker)
        
        # Broadcast update
        try:
            await broadcast_tracker_updated(db_tracker)
        except Exception:
            pass
        
        return {
            "success": True,
            "comment_id": new_comment.id,
            "status_updates": status_updates,
            "tracker": sqlalchemy_to_dict(db_tracker)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comment-with-status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment with status: {str(e)}"
        )


@router.get("/{tracker_id}/status-history", response_model=List[StatusHistoryResponse])
async def get_status_history(
    *,
    db: AsyncSession = Depends(get_db),
    tracker_id: int,
    status_field: Optional[str] = Query(None, description="Filter by 'production' or 'qc'"),
    current_user: UserModel = Depends(get_current_user),
) -> List[StatusHistoryResponse]:
    """
    Get status change history for a tracker.
    
    Returns a timeline of status changes with duration tracking.
    """
    from sqlalchemy import select
    
    try:
        # Verify tracker exists
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )
        
        # Build query
        query = (
            select(TrackerStatusHistory)
            .where(TrackerStatusHistory.tracker_id == tracker_id)
            .order_by(TrackerStatusHistory.entered_at.desc())
        )
        
        if status_field:
            query = query.where(TrackerStatusHistory.status_field == status_field)
        
        result = await db.execute(query)
        history_entries = result.scalars().all()
        
        # Build response with user info
        response = []
        for entry in history_entries:
            username = None
            if entry.changed_by_user_id:
                changed_user = await user.get(db, id=entry.changed_by_user_id)
                if changed_user:
                    username = changed_user.username
            
            response.append(StatusHistoryResponse(
                id=entry.id,
                status_field=entry.status_field,
                status_value=entry.status_value,
                entered_at=entry.entered_at,
                exited_at=entry.exited_at,
                duration_seconds=entry.duration_seconds,
                changed_by_username=username
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status history: {str(e)}"
        )


@router.get("/{tracker_id}/permissions", response_model=Dict[str, bool])
async def get_tracker_permissions(
    *,
    db: AsyncSession = Depends(get_db),
    tracker_id: int,
    current_user: UserModel = Depends(get_current_user),
) -> Dict[str, bool]:
    """
    Get the current user's permissions for a tracker.
    
    Returns a dict indicating which fields the user can modify.
    Used by frontend to enable/disable UI controls.
    
    Includes Study LEAD permissions for users with LEAD role in the tracker's study.
    """
    try:
        # Get tracker
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )
        
        # Get user's study role for this tracker
        study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
        
        return TrackerWorkflowService.can_user_modify_tracker(current_user, db_tracker, study_role)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get permissions: {str(e)}"
        )


@router.put("/{tracker_id}/production-flag", response_model=ReportingEffortItemTracker)
async def update_production_flag(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    tracker_id: int,
    value: bool = Query(..., description="New value for in_production_flag"),
    current_user: UserModel = Depends(get_current_user),
) -> ReportingEffortItemTracker:
    """
    Update the in_production_flag for a tracker.
    
    The flag can only be True when both production and QC are completed.
    Only ADMIN, Study LEAD, or the assigned production programmer can update this flag.
    """
    try:
        # Get tracker
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )
        
        # Permission check: Admin, study lead, or production programmer can update in_production_flag
        is_admin = current_user.is_admin
        study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
        is_study_lead = is_study_admin(study_role)
        is_production_programmer = db_tracker.production_programmer_id == current_user.id
        if not is_admin and not is_study_lead and not is_production_programmer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators, study leads, or the assigned production programmer can update the in-production flag"
            )
        
        # Validate the flag change
        is_valid, error = TrackerWorkflowService.validate_prod_flag(db_tracker, value)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        # Update the flag
        db_tracker.in_production_flag = value
        db_tracker.updated_at = datetime.utcnow()
        db.add(db_tracker)
        await db.commit()
        await db.refresh(db_tracker)
        
        # Broadcast update
        try:
            await broadcast_tracker_updated(db_tracker)
        except Exception:
            pass
        
        return db_tracker
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating production flag: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update production flag: {str(e)}"
        )


@router.put("/{tracker_id}/milestones", response_model=Dict[str, Any])
async def update_tracker_milestones(
    *,
    db: AsyncSession = Depends(get_db),
    tracker_id: int,
    milestone_ids: List[int] = Query(default=[], description="List of milestone IDs to assign"),
    current_user: UserModel = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Update milestone assignments for a tracker.

    This replaces all manual milestone links for the tracker with the provided list.
    Subtype and tag-based links are not affected - only manual links are managed.

    Only admins, study leads, or the production programmer can update milestone assignments.
    """
    try:
        # Get tracker
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )

        # Permission check: Admin, study lead, or production programmer
        is_admin = current_user.is_admin
        study_role = await get_user_study_role_for_tracker(db, current_user, tracker_id)
        is_study_lead = is_study_admin(study_role)
        is_production_programmer = db_tracker.production_programmer_id == current_user.id
        if not is_admin and not is_study_lead and not is_production_programmer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators, study leads, or the assigned production programmer can update milestone assignments"
            )

        # Update milestone assignments
        result = await milestone_tracker_assignment.update_tracker_milestones(
            db,
            tracker_id=tracker_id,
            milestone_ids=milestone_ids
        )

        # Broadcast update
        try:
            await broadcast_tracker_updated(db_tracker)
        except Exception:
            pass

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tracker milestones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tracker milestones: {str(e)}"
        )


@router.get("/{tracker_id}/milestones", response_model=List[int])
async def get_tracker_milestones(
    *,
    db: AsyncSession = Depends(get_db),
    tracker_id: int,
    current_user: UserModel = Depends(get_current_user),
) -> List[int]:
    """
    Get manual milestone assignments for a tracker.

    Returns list of milestone IDs that are manually linked to this tracker.
    """
    try:
        # Get tracker to verify it exists
        db_tracker = await reporting_effort_item_tracker.get(db, id=tracker_id)
        if not db_tracker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tracker not found"
            )

        # Get milestone IDs
        milestone_ids = await milestone_tracker_assignment.get_milestone_ids_by_tracker(
            db, tracker_id=tracker_id
        )

        return milestone_ids

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tracker milestones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tracker milestones: {str(e)}"
        )


# ========================================================================
# MAINTENANCE ENDPOINTS (Admin only)
# ========================================================================

@router.post("/maintenance/backfill-trackers", response_model=Dict[str, Any])
async def backfill_missing_trackers(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    reporting_effort_id: Optional[int] = Query(None, description="Optional: backfill only for this effort"),
) -> Dict[str, Any]:
    """
    Create tracker records for reporting effort items that don't have them.
    
    This is a maintenance endpoint to fix data inconsistency where items
    were created without corresponding tracker records.
    
    Admin only.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can run maintenance operations"
        )
    
    try:
        result = await reporting_effort_item_tracker.backfill_missing_trackers(
            db,
            reporting_effort_id=reporting_effort_id
        )
        
        logger.info(f"Backfill trackers: created {result['created_count']}, "
                    f"already existed {result['already_existed']}, "
                    f"total items {result['total_items']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error backfilling trackers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to backfill trackers: {str(e)}"
        )