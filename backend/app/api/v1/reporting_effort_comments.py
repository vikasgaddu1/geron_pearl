"""Reporting Effort Tracker Comments API endpoints."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.crud import reporting_effort_tracker_comment, reporting_effort_item, user, audit_log
from app.db.session import get_db
from app.schemas.reporting_effort_tracker_comment import (
    ReportingEffortTrackerComment,
    ReportingEffortTrackerCommentCreate,
    ReportingEffortTrackerCommentUpdate,
    ReportingEffortTrackerCommentWithDetails
)
from app.models.reporting_effort_tracker_comment import CommentType
from app.models.user import UserRole
from app.utils import sqlalchemy_to_dict
from app.api.v1.websocket import manager

# WebSocket broadcasting functions
async def broadcast_comment_created(comment_data):
    """Broadcast that a new comment was created."""
    try:
        message_data = {
            "type": "tracker_comment_created",
            "data": sqlalchemy_to_dict(comment_data)
        }
        await manager.broadcast(str(message_data).replace("'", '"'))
    except Exception as e:
        print(f"WebSocket broadcast error: {e}")

async def broadcast_comment_updated(comment_data):
    """Broadcast that a comment was updated."""
    try:
        message_data = {
            "type": "tracker_comment_updated",
            "data": sqlalchemy_to_dict(comment_data)
        }
        await manager.broadcast(str(message_data).replace("'", '"'))
    except Exception as e:
        print(f"WebSocket broadcast error: {e}")

async def broadcast_comment_deleted(comment_data):
    """Broadcast that a comment was deleted."""
    try:
        message_data = {
            "type": "tracker_comment_deleted",
            "data": sqlalchemy_to_dict(comment_data)
        }
        await manager.broadcast(str(message_data).replace("'", '"'))
    except Exception as e:
        print(f"WebSocket broadcast error: {e}")

router = APIRouter()

# Helper Functions
def get_current_user_id(request: Request) -> Optional[int]:
    """Extract user ID from request state (would be set by auth middleware)."""
    # First try request state (production)
    user_id = getattr(request.state, 'user_id', None)
    if user_id:
        return user_id
    
    # Fallback to header for testing
    header_user_id = request.headers.get('X-User-Id')
    if header_user_id:
        try:
            return int(header_user_id)
        except ValueError:
            pass
    
    return None

def get_current_user_role(request: Request) -> Optional[UserRole]:
    """Extract user role from request state (would be set by auth middleware)."""
    return getattr(request.state, 'user_role', None)

# Request/Response Schemas
class CommentCreateRequest(BaseModel):
    """Schema for creating a comment with automatic type detection."""
    reporting_effort_item_id: Optional[int] = Field(None, description="ID of the reporting effort item")
    tracker_id: Optional[int] = Field(None, description="ID of the tracker (will be converted to item ID)")
    comment_text: str = Field(..., min_length=1, description="Comment content")
    comment_type: Optional[str] = Field(None, description="Explicit comment type (overrides auto-detection)")
    comment_category: str = Field("general", description="Category: general, production, qc, issue, resolution")
    parent_comment_id: Optional[int] = Field(None, description="ID of parent comment for threading")

class CommentModerationRequest(BaseModel):
    """Schema for comment moderation actions."""
    action: str = Field(..., description="Moderation action: pin, unpin, delete")
    reason: Optional[str] = Field(None, description="Reason for moderation action")

# CRUD Endpoints
@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_comment(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    comment_request: CommentCreateRequest,
) -> dict:
    """
    Create a new comment with automatic role-based type assignment.
    """
    try:
        # Get current user info (in production, this would come from auth middleware)
        current_user_id = get_current_user_id(request)
        current_user_role = get_current_user_role(request)
        
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Determine item ID (either directly provided or via tracker)
        item_id = comment_request.reporting_effort_item_id
        if not item_id and comment_request.tracker_id:
            # Convert tracker_id to reporting_effort_item_id
            from app.crud.reporting_effort_item_tracker import reporting_effort_item_tracker
            tracker = await reporting_effort_item_tracker.get(db, id=comment_request.tracker_id)
            if not tracker:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tracker not found"
                )
            item_id = tracker.reporting_effort_item_id
        
        if not item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either reporting_effort_item_id or tracker_id must be provided"
            )
        
        # Verify item exists
        db_item = await reporting_effort_item.get(db, id=item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort item not found"
            )
        
        # Verify user exists
        db_user = await user.get(db, id=current_user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Determine comment type (explicit override or based on user role)
        comment_type = CommentType.BIOSTAT_COMMENT  # Default
        
        if comment_request.comment_type:
            # Use explicit comment type if provided
            try:
                comment_type = CommentType(comment_request.comment_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid comment type: {comment_request.comment_type}"
                )
        elif current_user_role in [UserRole.ADMIN, UserRole.EDITOR]:
            # These roles can create programmer comments
            comment_type = CommentType.PROGRAMMER_COMMENT
        
        # Verify parent comment exists if specified
        if comment_request.parent_comment_id:
            parent_comment = await reporting_effort_tracker_comment.get(
                db, id=comment_request.parent_comment_id
            )
            if not parent_comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent comment not found"
                )
        
        # Create the comment
        print(f"DEBUG: Creating comment with type {comment_type} ({type(comment_type)})")
        comment_create = ReportingEffortTrackerCommentCreate(
            reporting_effort_item_id=item_id,
            comment_text=comment_request.comment_text,
            comment_type=comment_type,
            parent_comment_id=comment_request.parent_comment_id
        )
        print(f"DEBUG: Comment create object: {comment_create}")
        
        created_comment = await reporting_effort_tracker_comment.create(
            db,
            obj_in=comment_create,
            user_id=current_user_id,
            user_role=current_user_role or UserRole.VIEWER
        )
        print(f"DEBUG: Created comment: {created_comment}")
        
        print(f"Comment created successfully: ID {created_comment.id} by user {current_user_id}")
        
        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_tracker_comments",
                record_id=created_comment.id,
                action="CREATE",
                user_id=current_user_id,
                changes={
                    "created": sqlalchemy_to_dict(created_comment),
                    "comment_type": comment_type.value,
                    "item_id": comment_request.reporting_effort_item_id
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket event
        try:
            await broadcast_comment_created(created_comment)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        # Return dict to avoid serialization issues
        return {
            "id": created_comment.id,
            "reporting_effort_item_id": created_comment.reporting_effort_item_id,
            "user_id": created_comment.user_id,
            "comment_text": created_comment.comment_text,
            "comment_type": created_comment.comment_type.value,
            "parent_comment_id": created_comment.parent_comment_id,
            "created_at": created_comment.created_at.isoformat(),
            "updated_at": created_comment.updated_at.isoformat() if created_comment.updated_at else None
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment: {str(e)}"
        )

@router.get("/", response_model=List[ReportingEffortTrackerComment])
async def read_comments(
    *,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> List[ReportingEffortTrackerComment]:
    """
    Retrieve comments with pagination.
    """
    try:
        return await reporting_effort_tracker_comment.get_multi(db, skip=skip, limit=limit)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comments"
        )

@router.get("/{comment_id}", response_model=ReportingEffortTrackerCommentWithDetails)
async def read_comment(
    *,
    db: AsyncSession = Depends(get_db),
    comment_id: int,
    include_thread: bool = Query(False, description="Include full reply thread"),
) -> ReportingEffortTrackerCommentWithDetails:
    """
    Get a specific comment by ID, optionally with its full thread.
    """
    try:
        if include_thread:
            db_comment = await reporting_effort_tracker_comment.get_thread(
                db, comment_id=comment_id, include_deleted=False
            )
        else:
            db_comment = await reporting_effort_tracker_comment.get(db, id=comment_id)
        
        if not db_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        return ReportingEffortTrackerCommentWithDetails.model_validate(db_comment)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comment"
        )

@router.get("/by-item/{item_id}", response_model=List[ReportingEffortTrackerCommentWithDetails])
async def read_comments_by_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
    include_deleted: bool = Query(False, description="Include soft-deleted comments"),
) -> List[ReportingEffortTrackerCommentWithDetails]:
    """
    Get all comments for a specific reporting effort item with threading.
    """
    try:
        # Verify item exists
        db_item = await reporting_effort_item.get(db, id=item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort item not found"
            )
        
        comments = await reporting_effort_tracker_comment.get_by_item(
            db, 
            reporting_effort_item_id=item_id,
            include_deleted=include_deleted
        )
        
        return [ReportingEffortTrackerCommentWithDetails.model_validate(c) for c in comments]
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comments for item"
        )

@router.get("/by-user/{user_id}", response_model=List[ReportingEffortTrackerComment])
async def read_comments_by_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    comment_type: Optional[CommentType] = Query(None, description="Filter by comment type"),
) -> List[ReportingEffortTrackerComment]:
    """
    Get all comments by a specific user.
    """
    try:
        # Verify user exists
        db_user = await user.get(db, id=user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return await reporting_effort_tracker_comment.get_by_user(
            db, user_id=user_id, comment_type=comment_type
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user comments"
        )

@router.get("/recent-activity", response_model=List[ReportingEffortTrackerCommentWithDetails])
async def read_recent_activity(
    *,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="Number of recent comments to retrieve"),
) -> List[ReportingEffortTrackerCommentWithDetails]:
    """
    Get recent comment activity across all items.
    """
    try:
        comments = await reporting_effort_tracker_comment.get_recent_activity(db, limit=limit)
        return [ReportingEffortTrackerCommentWithDetails.model_validate(c) for c in comments]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent activity"
        )

@router.put("/{comment_id}", response_model=ReportingEffortTrackerComment)
async def update_comment(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    comment_id: int,
    comment_in: ReportingEffortTrackerCommentUpdate,
) -> ReportingEffortTrackerComment:
    """
    Update a comment (only by the original author).
    """
    try:
        current_user_id = get_current_user_id(request)
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        db_comment = await reporting_effort_tracker_comment.get(db, id=comment_id)
        if not db_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Store original data for audit
        original_data = sqlalchemy_to_dict(db_comment)
        
        updated_comment = await reporting_effort_tracker_comment.update(
            db, db_obj=db_comment, obj_in=comment_in, user_id=current_user_id
        )
        
        print(f"Comment updated successfully: ID {updated_comment.id}")
        
        # Log audit trail
        try:
            changes = {
                "before": original_data,
                "after": sqlalchemy_to_dict(updated_comment)
            }
            await audit_log.log_action(
                db,
                table_name="reporting_effort_tracker_comments",
                record_id=updated_comment.id,
                action="UPDATE",
                user_id=current_user_id,
                changes=changes,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket event
        try:
            await broadcast_comment_updated(updated_comment)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return updated_comment
        
    except ValueError as e:
        # Handle permission errors from CRUD
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update comment"
        )

@router.delete("/{comment_id}", response_model=ReportingEffortTrackerComment)
async def delete_comment(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    comment_id: int,
) -> ReportingEffortTrackerComment:
    """
    Soft delete a comment (only by author or admin).
    """
    try:
        current_user_id = get_current_user_id(request)
        current_user_role = get_current_user_role(request)
        
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Store data for audit and broadcast
        db_comment = await reporting_effort_tracker_comment.get(db, id=comment_id)
        if not db_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        comment_data = sqlalchemy_to_dict(db_comment)
        
        deleted_comment = await reporting_effort_tracker_comment.soft_delete(
            db, 
            id=comment_id, 
            user_id=current_user_id,
            user_role=current_user_role or UserRole.VIEWER
        )
        
        print(f"Comment soft deleted successfully: ID {deleted_comment.id}")
        
        # Log audit trail
        try:
            await audit_log.log_action(
                db,
                table_name="reporting_effort_tracker_comments",
                record_id=deleted_comment.id,
                action="SOFT_DELETE",
                user_id=current_user_id,
                changes={
                    "deleted": comment_data,
                    "deleted_by": current_user_id
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket event
        try:
            await broadcast_comment_deleted(deleted_comment)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return deleted_comment
        
    except ValueError as e:
        # Handle permission errors from CRUD
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete comment"
        )

# Moderation Endpoints
@router.post("/{comment_id}/moderate", response_model=ReportingEffortTrackerComment)
async def moderate_comment(
    *,
    db: AsyncSession = Depends(get_db),
    request: Request,
    comment_id: int,
    moderation: CommentModerationRequest,
    # Note: In production, add admin role authentication here
    # current_user: User = Depends(get_current_admin_user)
) -> ReportingEffortTrackerComment:
    """
    Perform moderation actions on a comment.
    Admin only functionality.
    """
    try:
        current_user_id = get_current_user_id(request)
        current_user_role = get_current_user_role(request)
        
        if not current_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Verify admin role (in production)
        if current_user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for moderation"
            )
        
        db_comment = await reporting_effort_tracker_comment.get(db, id=comment_id)
        if not db_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Store original data for audit
        original_data = sqlalchemy_to_dict(db_comment)
        
        # Perform moderation action
        if moderation.action == "pin":
            update_data = ReportingEffortTrackerCommentUpdate(is_pinned=True)
        elif moderation.action == "unpin":
            update_data = ReportingEffortTrackerCommentUpdate(is_pinned=False)
        elif moderation.action == "delete":
            # Use soft delete function
            return await reporting_effort_tracker_comment.soft_delete(
                db,
                id=comment_id,
                user_id=current_user_id,
                user_role=current_user_role
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid moderation action. Use 'pin', 'unpin', or 'delete'"
            )
        
        # Apply the moderation update
        moderated_comment = await reporting_effort_tracker_comment.update(
            db, db_obj=db_comment, obj_in=update_data, user_id=current_user_id
        )
        
        print(f"Comment moderated successfully: ID {moderated_comment.id}, action: {moderation.action}")
        
        # Log audit trail
        try:
            changes = {
                "moderation": {
                    "action": moderation.action,
                    "reason": moderation.reason,
                    "moderator_id": current_user_id
                },
                "before": original_data,
                "after": sqlalchemy_to_dict(moderated_comment)
            }
            await audit_log.log_action(
                db,
                table_name="reporting_effort_tracker_comments",
                record_id=moderated_comment.id,
                action=f"MODERATE_{moderation.action.upper()}",
                user_id=current_user_id,
                changes=changes,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as audit_error:
            print(f"Audit logging error: {audit_error}")
        
        # Broadcast WebSocket event
        try:
            await broadcast_comment_updated(moderated_comment)
        except Exception as ws_error:
            print(f"WebSocket broadcast error: {ws_error}")
        
        return moderated_comment
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to moderate comment: {str(e)}"
        )

# Statistics and Analytics
@router.get("/statistics/by-item/{item_id}", response_model=Dict[str, Any])
async def get_item_comment_statistics(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
) -> Dict[str, Any]:
    """
    Get comment statistics for a specific item.
    """
    try:
        # Verify item exists
        db_item = await reporting_effort_item.get(db, id=item_id)
        if not db_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting effort item not found"
            )
        
        # Get all comments for the item
        comments = await reporting_effort_tracker_comment.get_by_item(
            db, reporting_effort_item_id=item_id, include_deleted=True
        )
        
        # Calculate statistics
        total_comments = len(comments)
        active_comments = len([c for c in comments if not c.is_deleted])
        deleted_comments = total_comments - active_comments
        
        by_type = {}
        by_user = {}
        by_category = {}
        
        for comment in comments:
            if not comment.is_deleted:  # Only count active comments
                # Count by type
                comment_type = comment.comment_type or "unknown"
                by_type[comment_type] = by_type.get(comment_type, 0) + 1
                
                # Count by user
                user_id = str(comment.user_id)
                by_user[user_id] = by_user.get(user_id, 0) + 1
                
                # Count by category
                category = comment.comment_category or "general"
                by_category[category] = by_category.get(category, 0) + 1
        
        return {
            "item_id": item_id,
            "total_comments": total_comments,
            "active_comments": active_comments,
            "deleted_comments": deleted_comments,
            "by_type": by_type,
            "by_user": by_user,
            "by_category": by_category,
            "has_pinned_comments": any(c.is_pinned for c in comments if not c.is_deleted),
            "thread_count": len([c for c in comments if c.parent_comment_id is None and not c.is_deleted])
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comment statistics: {str(e)}"
        )

@router.get("/statistics/overall", response_model=Dict[str, Any])
async def get_overall_comment_statistics(
    *,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000, description="Limit for recent analysis"),
) -> Dict[str, Any]:
    """
    Get overall comment system statistics.
    """
    try:
        # Get recent comments for analysis
        recent_comments = await reporting_effort_tracker_comment.get_multi(
            db, skip=0, limit=limit
        )
        
        # Basic statistics
        total_comments = len(recent_comments)
        active_comments = len([c for c in recent_comments if not c.is_deleted])
        
        # Analysis by type and category
        by_type = {}
        by_category = {}
        unique_users = set()
        unique_items = set()
        
        for comment in recent_comments:
            if not comment.is_deleted:
                # Count by type
                comment_type = comment.comment_type or "unknown"
                by_type[comment_type] = by_type.get(comment_type, 0) + 1
                
                # Count by category
                category = comment.comment_category or "general"
                by_category[category] = by_category.get(category, 0) + 1
                
                # Track unique users and items
                unique_users.add(comment.user_id)
                unique_items.add(comment.reporting_effort_item_id)
        
        return {
            "analysis_scope": f"Recent {limit} comments",
            "total_comments_analyzed": total_comments,
            "active_comments": active_comments,
            "deleted_comments": total_comments - active_comments,
            "unique_users_active": len(unique_users),
            "unique_items_with_comments": len(unique_items),
            "by_type": by_type,
            "by_category": by_category,
            "average_comments_per_user": active_comments / len(unique_users) if unique_users else 0,
            "average_comments_per_item": active_comments / len(unique_items) if unique_items else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get overall statistics: {str(e)}"
        )