"""
Simplified Tracker Comments API Endpoints
Blog-style comment system with real-time WebSocket updates
"""

from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
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
    """
    Create a new comment (parent or reply)
    
    - Creates parent comment if parent_comment_id is None
    - Creates reply if parent_comment_id is provided
    - Automatically updates unresolved_comment_count for parent comments
    - Broadcasts WebSocket event for real-time updates
    """
    try:
        # Create the comment
        created_comment = await tracker_comment.create(
            db=db, 
            obj_in=obj_in, 
            user_id=current_user_id
        )
        
        # Get the comment with user information for response
        comments_with_users = await tracker_comment.get_by_tracker_id(
            db=db, 
            tracker_id=obj_in.tracker_id
        )
        
        # Find the created comment in the response
        created_comment_with_user = None
        for comment in comments_with_users:
            if comment.id == created_comment.id:
                created_comment_with_user = comment
                break
        
        if not created_comment_with_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created comment"
            )
        
        # Get current unresolved count for WebSocket broadcast
        unresolved_count = await tracker_comment.get_unresolved_count(
            db=db, 
            tracker_id=obj_in.tracker_id
        )
        
        # Broadcast WebSocket event
        if obj_in.parent_comment_id is None:
            # Parent comment created
            await broadcast_comment_created(
                tracker_id=obj_in.tracker_id,
                comment_data=created_comment_with_user,
                unresolved_count=unresolved_count
            )
        else:
            # Reply created
            await broadcast_comment_replied(
                tracker_id=obj_in.tracker_id,
                parent_comment_id=obj_in.parent_comment_id,
                comment_data=created_comment_with_user,
                unresolved_count=unresolved_count
            )
        
        return created_comment_with_user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.get("/tracker/{tracker_id}", response_model=List[CommentWithUserInfo])
async def get_comments_for_tracker(
    tracker_id: int,
    db: AsyncSession = Depends(get_db)
) -> List[CommentWithUserInfo]:
    """
    Get all comments for a tracker with username information
    
    Returns comments in chronological order with user details.
    Suitable for blog-style display with threading.
    """
    try:
        comments = await tracker_comment.get_by_tracker_id(
            db=db, 
            tracker_id=tracker_id
        )
        return comments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve comments: {str(e)}"
        )


@router.post("/{comment_id}/resolve", response_model=CommentWithUserInfo)
async def resolve_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
) -> CommentWithUserInfo:
    """
    Resolve a parent comment
    
    - Only parent comments (parent_comment_id = NULL) can be resolved
    - Automatically updates unresolved_comment_count on tracker
    - Broadcasts WebSocket event for real-time updates
    """
    try:
        # Resolve the comment (this will raise error if it's not a parent comment)
        resolved_comment = await tracker_comment.resolve_comment(
            db=db,
            comment_id=comment_id,
            resolved_by_user_id=current_user_id
        )
        
        # Get updated comment with user information
        comments_with_users = await tracker_comment.get_by_tracker_id(
            db=db, 
            tracker_id=resolved_comment.tracker_id
        )
        
        # Find the resolved comment in the response
        resolved_comment_with_user = None
        for comment in comments_with_users:
            if comment.id == comment_id:
                resolved_comment_with_user = comment
                break
        
        if not resolved_comment_with_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve resolved comment"
            )
        
        # Get updated unresolved count for WebSocket broadcast
        unresolved_count = await tracker_comment.get_unresolved_count(
            db=db, 
            tracker_id=resolved_comment.tracker_id
        )
        
        # Broadcast WebSocket event
        await broadcast_comment_resolved(
            tracker_id=resolved_comment.tracker_id,
            comment_id=comment_id,
            unresolved_count=unresolved_count
        )
        
        return resolved_comment_with_user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve comment: {str(e)}"
        )


@router.get("/tracker/{tracker_id}/unresolved-count", response_model=int)
async def get_unresolved_count(
    tracker_id: int,
    db: AsyncSession = Depends(get_db)
) -> int:
    """
    Get count of unresolved parent comments for a tracker
    
    Used for button badge display. Only counts parent comments,
    not replies.
    """
    try:
        count = await tracker_comment.get_unresolved_count(
            db=db, 
            tracker_id=tracker_id
        )
        return count
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unresolved count: {str(e)}"
        )


@router.get("/tracker/{tracker_id}/summary", response_model=TrackerCommentSummary)
async def get_comment_summary(
    tracker_id: int,
    db: AsyncSession = Depends(get_db)
) -> TrackerCommentSummary:
    """
    Get comment summary for a tracker
    
    Provides statistics about comments for dashboard and analytics.
    Includes separate counts for programming and biostat comments.
    """
    try:
        # Use the CRUD method that returns separate counts
        summary = await tracker_comment.get_comment_summary(
            db=db, 
            tracker_id=tracker_id
        )
        
        return TrackerCommentSummary(**summary)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comment summary: {str(e)}"
        )


@router.get("/tracker/{tracker_id}/threaded", response_model=List[Dict[str, Any]])
async def get_threaded_comments(
    tracker_id: int,
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get comments in threaded format for blog-style display
    
    Returns nested structure with replies grouped under parent comments.
    Suitable for rendering in R Shiny modal with proper indentation.
    """
    try:
        threaded_comments = await tracker_comment.get_comments_with_users(
            db=db, 
            tracker_id=tracker_id
        )
        return threaded_comments
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get threaded comments: {str(e)}"
        )