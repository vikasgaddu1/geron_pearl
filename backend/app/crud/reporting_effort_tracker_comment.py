"""CRUD operations for ReportingEffortTrackerComment."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reporting_effort_tracker_comment import ReportingEffortTrackerComment, CommentType
from app.models.user import UserRole
from app.schemas.reporting_effort_tracker_comment import (
    ReportingEffortTrackerCommentCreate,
    ReportingEffortTrackerCommentUpdate
)


class ReportingEffortTrackerCommentCRUD:
    """CRUD operations for ReportingEffortTrackerComment."""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: ReportingEffortTrackerCommentCreate,
        user_id: int,
        user_role: UserRole
    ) -> ReportingEffortTrackerComment:
        """
        Create a new comment with role validation.
        
        Args:
            db: Database session
            obj_in: Comment creation data
            user_id: ID of the user creating the comment
            user_role: Role of the user (for validation)
        
        Returns:
            Created comment
        
        Raises:
            ValueError: If user role doesn't match comment type
        """
        # Validate comment type based on user role
        if obj_in.comment_type == CommentType.programmer_comment:
            if user_role not in [UserRole.ADMIN, UserRole.EDITOR]:
                raise ValueError("Only ADMIN and EDITOR roles can create programmer comments")
        elif obj_in.comment_type == CommentType.biostat_comment:
            # All roles can create biostat comments
            pass
        
        db_obj = ReportingEffortTrackerComment(
            **obj_in.model_dump(),
            user_id=user_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[ReportingEffortTrackerComment]:
        """Get a single comment by ID."""
        result = await db.execute(
            select(ReportingEffortTrackerComment)
            .options(selectinload(ReportingEffortTrackerComment.user))
            .where(ReportingEffortTrackerComment.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportingEffortTrackerComment]:
        """Get multiple comments."""
        result = await db.execute(
            select(ReportingEffortTrackerComment)
            .options(selectinload(ReportingEffortTrackerComment.user))
            .offset(skip)
            .limit(limit)
            .order_by(ReportingEffortTrackerComment.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_item(
        self,
        db: AsyncSession,
        *,
        reporting_effort_item_id: int,
        include_deleted: bool = False
    ) -> List[ReportingEffortTrackerComment]:
        """
        Get all comments for a specific item.
        
        Args:
            db: Database session
            reporting_effort_item_id: ID of the reporting effort item
            include_deleted: Whether to include soft-deleted comments
        
        Returns:
            List of comments with thread structure
        """
        query = select(ReportingEffortTrackerComment).options(
            selectinload(ReportingEffortTrackerComment.user),
            selectinload(ReportingEffortTrackerComment.replies)
        ).where(
            ReportingEffortTrackerComment.reporting_effort_item_id == reporting_effort_item_id
        )
        
        if not include_deleted:
            query = query.where(ReportingEffortTrackerComment.is_deleted == False)
        
        # Get only top-level comments (no parent)
        query = query.where(ReportingEffortTrackerComment.parent_comment_id.is_(None))
        query = query.order_by(ReportingEffortTrackerComment.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_thread(
        self,
        db: AsyncSession,
        *,
        comment_id: int,
        include_deleted: bool = False
    ) -> Optional[ReportingEffortTrackerComment]:
        """
        Get a comment with its full reply thread.
        
        Args:
            db: Database session
            comment_id: ID of the root comment
            include_deleted: Whether to include soft-deleted comments
        
        Returns:
            Comment with nested replies
        """
        query = select(ReportingEffortTrackerComment).options(
            selectinload(ReportingEffortTrackerComment.user),
            selectinload(ReportingEffortTrackerComment.replies).selectinload(
                ReportingEffortTrackerComment.user
            )
        ).where(ReportingEffortTrackerComment.id == comment_id)
        
        if not include_deleted:
            query = query.where(ReportingEffortTrackerComment.is_deleted == False)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ReportingEffortTrackerComment,
        obj_in: ReportingEffortTrackerCommentUpdate,
        user_id: int
    ) -> ReportingEffortTrackerComment:
        """
        Update a comment (only by original author).
        
        Args:
            db: Database session
            db_obj: Comment to update
            obj_in: Update data
            user_id: ID of user attempting update
        
        Returns:
            Updated comment
        
        Raises:
            ValueError: If user is not the original author
        """
        if db_obj.user_id != user_id:
            raise ValueError("Only the original author can edit a comment")
        
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # Mark as edited
        db_obj.is_edited = True
        db_obj.updated_at = datetime.utcnow()
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def soft_delete(
        self,
        db: AsyncSession,
        *,
        id: int,
        user_id: int,
        user_role: UserRole
    ) -> Optional[ReportingEffortTrackerComment]:
        """
        Soft delete a comment.
        
        Args:
            db: Database session
            id: Comment ID
            user_id: ID of user attempting deletion
            user_role: Role of user (ADMIN can delete any comment)
        
        Returns:
            Soft-deleted comment
        
        Raises:
            ValueError: If user cannot delete the comment
        """
        db_obj = await self.get(db, id=id)
        
        if not db_obj:
            return None
        
        # Check permissions
        if user_role != UserRole.ADMIN and db_obj.user_id != user_id:
            raise ValueError("Only the original author or ADMIN can delete a comment")
        
        # Soft delete
        db_obj.is_deleted = True
        db_obj.deleted_at = datetime.utcnow()
        db_obj.deleted_by_id = user_id
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        comment_type: Optional[CommentType] = None
    ) -> List[ReportingEffortTrackerComment]:
        """Get all comments by a specific user."""
        query = select(ReportingEffortTrackerComment).where(
            ReportingEffortTrackerComment.user_id == user_id,
            ReportingEffortTrackerComment.is_deleted == False
        )
        
        if comment_type:
            query = query.where(ReportingEffortTrackerComment.comment_type == comment_type)
        
        query = query.order_by(ReportingEffortTrackerComment.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_activity(
        self,
        db: AsyncSession,
        *,
        limit: int = 10
    ) -> List[ReportingEffortTrackerComment]:
        """Get recent comment activity across all items."""
        result = await db.execute(
            select(ReportingEffortTrackerComment)
            .options(
                selectinload(ReportingEffortTrackerComment.user),
                selectinload(ReportingEffortTrackerComment.reporting_effort_item)
            )
            .where(ReportingEffortTrackerComment.is_deleted == False)
            .order_by(ReportingEffortTrackerComment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


# Create singleton instance
reporting_effort_tracker_comment = ReportingEffortTrackerCommentCRUD()