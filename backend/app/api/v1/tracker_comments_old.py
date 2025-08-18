"""
Simplified Tracker Comments API Endpoints
Blog-style comment system with real-time WebSocket updates
"""

from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.crud.tracker_comment import tracker_comment
from app.schemas.tracker_comment import (
    TrackerCommentCreate,
    TrackerComment, 
    TrackerCommentSummary,
    CommentWithUserInfo
)
from app.api.v1.websocket import (
    broadcast_comment_created,
    broadcast_comment_resolved,
    broadcast_comment_replied
)

router = APIRouter()


# Mock user authentication for demo purposes
# TODO: Replace with actual authentication system
async def get_current_user_id(x_user_id: int = Header(default=1)) -> int:
    """Get current user ID from header (mock authentication)"""
    return x_user_id


@router.post("/", response_model=CommentWithUserInfo, status_code=status.HTTP_201_CREATED)
async def create_comment(
    *,
    db: AsyncSession = Depends(get_db),
    obj_in: TrackerCommentCreate,
    current_user_id: int = Depends(get_current_user_id)
) -> CommentWithUserInfo:
    """Create a new comment"""
    try:
        comment = await tracker_comment.create_with_user(
            db=db, 
            obj_in=comment_in, 
            user_id=x_user_id
        )
        
        # Create response data before commit to avoid detachment issues
        response_data = TrackerCommentInDB(
            id=comment.id,
            tracker_id=comment.tracker_id,
            user_id=comment.user_id,
            parent_comment_id=comment.parent_comment_id,
            comment_text=comment.comment_text,
            comment_type=comment.comment_type,
            is_resolved=comment.is_resolved,
            is_pinned=comment.is_pinned,
            is_tracked=comment.is_tracked,
            is_deleted=comment.is_deleted,
            resolved_by_user_id=comment.resolved_by_user_id,
            resolved_at=comment.resolved_at,
            created_at=comment.created_at,
            updated_at=comment.updated_at
        )
        
        await db.commit()
        
        # Broadcast WebSocket event
        try:
            await broadcast_comment_created(comment)
        except Exception as ws_error:
            # Log WebSocket error but don't fail the request
            print(f"WebSocket broadcast error: {ws_error}")
        
        return response_data
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.get("/tracker/{tracker_id}", response_model=List[TrackerComment])
async def get_comments_by_tracker(
    tracker_id: int,
    include_deleted: bool = Query(False, description="Include deleted comments"),
    db: AsyncSession = Depends(get_db)
) -> List[TrackerComment]:
    """Get all comments for a specific tracker item"""
    if tracker_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tracker ID"
        )
    
    comments = await tracker_comment.get_by_tracker_id(
        db=db, 
        tracker_id=tracker_id, 
        include_deleted=include_deleted
    )
    return comments


@router.get("/summary", response_model=Dict[int, CommentSummary])
async def get_comments_summary(
    tracker_ids: List[int] = Query(..., description="List of tracker IDs"),
    db: AsyncSession = Depends(get_db)
) -> Dict[int, CommentSummary]:
    """Get comment summaries for multiple tracker items"""
    if not tracker_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one tracker ID is required"
        )
    
    if len(tracker_ids) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many tracker IDs (max 1000)"
        )
    
    summaries = await tracker_comment.get_comments_summary(
        db=db, 
        tracker_ids=tracker_ids
    )
    return summaries


@router.get("/{comment_id}", response_model=TrackerComment)
async def get_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db)
) -> TrackerComment:
    """Get a specific comment by ID"""
    comment = await tracker_comment.get(db, id=comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    if comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment has been deleted"
        )
    
    return comment


@router.put("/{comment_id}", response_model=TrackerComment)
async def update_comment(
    comment_id: int,
    comment_update: TrackerCommentUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_id: int = Header(..., alias="X-User-Id"),
    x_user_role: str = Header(..., alias="X-User-Role")
) -> TrackerComment:
    """Update a comment"""
    comment = await tracker_comment.get(db, id=comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    if comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update deleted comment"
        )
    
    # Check permissions (user can only edit their own comments, admins can edit any)
    if comment.user_id != x_user_id and x_user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this comment"
        )
    
    try:
        updated_comment = await tracker_comment.update(
            db=db, 
            db_obj=comment, 
            obj_in=comment_update
        )
        await db.commit()
        
        # Broadcast WebSocket event
        await broadcast_comment_updated(updated_comment)
        
        return updated_comment
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update comment: {str(e)}"
        )


@router.post("/{comment_id}/resolve", response_model=TrackerComment)
async def resolve_comment(
    comment_id: int,
    resolve_data: CommentResolve,
    db: AsyncSession = Depends(get_db),
    x_user_id: int = Header(..., alias="X-User-Id"),
    x_user_role: str = Header(..., alias="X-User-Role")
) -> TrackerComment:
    """Mark a comment as resolved or unresolved"""
    comment = await tracker_comment.mark_resolved(
        db=db,
        comment_id=comment_id,
        user_id=x_user_id,
        is_resolved=resolve_data.is_resolved
    )
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    await db.commit()
    
    # Broadcast WebSocket event
    await broadcast_comment_resolved(comment)
    
    return comment


@router.post("/{comment_id}/pin", response_model=TrackerComment)
async def toggle_pin_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    x_user_id: int = Header(..., alias="X-User-Id"),
    x_user_role: str = Header(..., alias="X-User-Role")
) -> TrackerComment:
    """Toggle pin status of a comment"""
    # Check if user has permission to pin (admin or comment owner)
    comment = await tracker_comment.get(db, id=comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    if comment.user_id != x_user_id and x_user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to pin this comment"
        )
    
    pinned_comment = await tracker_comment.toggle_pin(db=db, comment_id=comment_id)
    await db.commit()
    
    # Broadcast WebSocket event
    await broadcast_comment_updated(pinned_comment)
    
    return pinned_comment


@router.post("/{comment_id}/unpin", response_model=TrackerComment)
async def unpin_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    x_user_id: int = Header(..., alias="X-User-Id"),
    x_user_role: str = Header(..., alias="X-User-Role")
) -> TrackerComment:
    """Unpin a pinned comment"""
    # Check if user has permission to unpin (admin or comment owner)
    comment = await tracker_comment.get(db, id=comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    if comment.user_id != x_user_id and x_user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to unpin this comment"
        )
    
    # Only unpin if the comment is currently pinned
    if not comment.is_pinned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment is not currently pinned"
        )
    
    # Use the existing toggle_pin method to unpin
    unpinned_comment = await tracker_comment.toggle_pin(db=db, comment_id=comment_id)
    await db.commit()
    
    # Broadcast WebSocket event
    await broadcast_comment_updated(unpinned_comment)
    
    return unpinned_comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    hard_delete: bool = Query(False, description="Permanently delete comment"),
    db: AsyncSession = Depends(get_db),
    x_user_id: int = Header(..., alias="X-User-Id"),
    x_user_role: str = Header(..., alias="X-User-Role")
) -> None:
    """Delete a comment (soft delete by default)"""
    comment = await tracker_comment.get(db, id=comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Check permissions
    if comment.user_id != x_user_id and x_user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    try:
        if hard_delete and x_user_role == "ADMIN":
            # Hard delete (admin only)
            await tracker_comment.remove(db=db, id=comment_id)
        else:
            # Soft delete
            await tracker_comment.soft_delete(db=db, comment_id=comment_id)
        
        await db.commit()
        
        # Broadcast WebSocket event
        await broadcast_comment_deleted(comment)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete comment: {str(e)}"
        )


@router.post("/search", response_model=List[TrackerComment])
async def search_comments(
    filter_params: CommentFilter,
    skip: int = Query(0, ge=0, description="Number of comments to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of comments to return"),
    db: AsyncSession = Depends(get_db)
) -> List[TrackerComment]:
    """Search comments with filters"""
    comments = await tracker_comment.search_comments(
        db=db,
        filter_params=filter_params,
        skip=skip,
        limit=limit
    )
    return comments


@router.get("/thread/{parent_comment_id}", response_model=List[TrackerComment])
async def get_comment_thread(
    parent_comment_id: int,
    db: AsyncSession = Depends(get_db)
) -> List[TrackerComment]:
    """Get all replies in a comment thread"""
    replies = await tracker_comment.get_thread_comments(
        db=db, 
        parent_comment_id=parent_comment_id
    )
    return replies


@router.get("/user/{user_id}/stats", response_model=Dict[str, Any])
async def get_user_comment_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    x_user_id: int = Header(..., alias="X-User-Id"),
    x_user_role: str = Header(..., alias="X-User-Role")
) -> Dict[str, Any]:
    """Get comment statistics for a user"""
    # Users can only see their own stats unless they're admin
    if user_id != x_user_id and x_user_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view user statistics"
        )
    
    stats = await tracker_comment.get_user_stats(db=db, user_id=user_id)
    return stats