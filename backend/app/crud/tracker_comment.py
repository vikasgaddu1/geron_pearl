"""
Simplified CRUD operations for TrackerComment model
Blog-style comment system with automatic unresolved comment count management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tracker_comment import TrackerComment
from app.models.user import User
from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
from app.schemas.tracker_comment import TrackerCommentCreate, CommentWithUserInfo


class TrackerCommentCRUD:
    """Simplified CRUD operations for tracker comments with automatic count management."""

    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: TrackerCommentCreate, 
        user_id: int
    ) -> TrackerComment:
        """
        Create new comment and automatically update unresolved_comment_count on tracker.
        Only increment count if it's a parent comment (parent_comment_id is None).
        """
        try:
            # Create the comment
            obj_data = obj_in.model_dump()
            # Explicitly set user_id - don't rely on obj_data
            obj_data["user_id"] = user_id
            
            # Ensure user_id is not None and is the correct value
            if obj_data.get("user_id") != user_id:
                obj_data["user_id"] = user_id
            
            db_obj = TrackerComment(
                tracker_id=obj_data["tracker_id"],
                user_id=user_id,  # Explicitly set user_id
                comment_text=obj_data["comment_text"],
                comment_type=obj_data.get("comment_type", "programming"),
                parent_comment_id=obj_data.get("parent_comment_id"),
                is_resolved=False
            )
            db.add(db_obj)
            await db.flush()  # Get the ID without committing
            
            # Update unresolved comment count if this is a parent comment
            if obj_data.get("parent_comment_id") is None:  # Parent comment only
                tracker = await db.execute(
                    select(ReportingEffortItemTracker)
                    .where(ReportingEffortItemTracker.id == obj_data["tracker_id"])
                )
                tracker_obj = tracker.scalar_one_or_none()
                
                if tracker_obj:
                    tracker_obj.unresolved_comment_count = tracker_obj.unresolved_comment_count + 1
                    db.add(tracker_obj)
            
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
            
        except Exception as e:
            await db.rollback()
            raise e

    async def get_by_tracker_id(
        self, 
        db: AsyncSession, 
        *, 
        tracker_id: int
    ) -> List[CommentWithUserInfo]:
        """
        Get all comments for a tracker with username information (JOIN with Users table).
        Return in chronological order with all necessary fields for blog-style display.
        """
        query = select(
            TrackerComment.id,
            TrackerComment.tracker_id,
            TrackerComment.user_id,
            User.username,
            TrackerComment.parent_comment_id,
            TrackerComment.comment_text,
            TrackerComment.comment_type,
            TrackerComment.is_resolved,
            TrackerComment.resolved_by_user_id,
            User.username.label("resolved_by_username"),  # Will be overridden by join
            TrackerComment.resolved_at,
            TrackerComment.created_at,
            TrackerComment.updated_at
        ).select_from(
            TrackerComment.__table__.join(
                User.__table__, 
                TrackerComment.user_id == User.id
            ).outerjoin(
                User.__table__.alias("resolved_user"),
                TrackerComment.resolved_by_user_id == User.id
            )
        ).where(
            TrackerComment.tracker_id == tracker_id
        ).order_by(TrackerComment.created_at.asc())
        
        result = await db.execute(query)
        rows = result.all()
        
        # Convert to CommentWithUserInfo objects
        comments = []
        for row in rows:
            # Get resolved_by_username if exists
            resolved_by_username = None
            if row.resolved_by_user_id:
                resolved_user_result = await db.execute(
                    select(User.username).where(User.id == row.resolved_by_user_id)
                )
                resolved_user = resolved_user_result.scalar_one_or_none()
                if resolved_user:
                    resolved_by_username = resolved_user
            
            comment_data = CommentWithUserInfo(
                id=row.id,
                tracker_id=row.tracker_id,
                user_id=row.user_id,
                username=row.username,
                parent_comment_id=row.parent_comment_id,
                comment_text=row.comment_text,
                comment_type=row.comment_type or "programming",
                is_resolved=row.is_resolved,
                resolved_by_user_id=row.resolved_by_user_id,
                resolved_by_username=resolved_by_username,
                resolved_at=row.resolved_at,
                created_at=row.created_at,
                updated_at=row.updated_at,
                is_parent_comment=(row.parent_comment_id is None)
            )
            comments.append(comment_data)
            
        return comments

    async def resolve_comment(
        self, 
        db: AsyncSession, 
        *, 
        comment_id: int, 
        resolved_by_user_id: int
    ) -> Optional[TrackerComment]:
        """
        Only allow resolving parent comments (parent_comment_id = NULL).
        Update unresolved_comment_count on tracker when resolved.
        Set resolved_at timestamp.
        """
        try:
            # Get the comment with tracker relationship
            comment_result = await db.execute(
                select(TrackerComment)
                .options(selectinload(TrackerComment.tracker))
                .where(TrackerComment.id == comment_id)
            )
            comment = comment_result.scalar_one_or_none()
            
            if not comment:
                return None
            
            # Only allow resolving parent comments
            if comment.parent_comment_id is not None:
                raise ValueError("Only parent comments can be resolved")
            
            # Don't resolve if already resolved
            if comment.is_resolved:
                return comment
            
            # Update comment resolution
            comment.is_resolved = True
            comment.resolved_by_user_id = resolved_by_user_id
            comment.resolved_at = func.now()
            
            # Update tracker unresolved count
            tracker = await db.execute(
                select(ReportingEffortItemTracker)
                .where(ReportingEffortItemTracker.id == comment.tracker_id)
            )
            tracker_obj = tracker.scalar_one_or_none()
            
            if tracker_obj and tracker_obj.unresolved_comment_count > 0:
                tracker_obj.unresolved_comment_count = tracker_obj.unresolved_comment_count - 1
                db.add(tracker_obj)
            
            db.add(comment)
            await db.commit()
            await db.refresh(comment)
            return comment
            
        except Exception as e:
            await db.rollback()
            raise e

    async def get_unresolved_count(
        self, 
        db: AsyncSession, 
        *, 
        tracker_id: int
    ) -> int:
        """
        Get count of unresolved parent comments only (for button badge).
        """
        result = await db.execute(
            select(func.count(TrackerComment.id))
            .where(
                and_(
                    TrackerComment.tracker_id == tracker_id,
                    TrackerComment.parent_comment_id.is_(None),  # Parent comments only
                    TrackerComment.is_resolved == False
                )
            )
        )
        return result.scalar() or 0

    async def get_comments_with_users(
        self, 
        db: AsyncSession, 
        *, 
        tracker_id: int
    ) -> List[Dict[str, Any]]:
        """
        Enhanced version with full user details.
        Include nested structure for blog-style threading.
        """
        # Get all comments for the tracker with user information
        query = select(TrackerComment).options(
            selectinload(TrackerComment.user),
            selectinload(TrackerComment.resolved_by_user)
        ).where(
            TrackerComment.tracker_id == tracker_id
        ).order_by(TrackerComment.created_at.asc())
        
        result = await db.execute(query)
        all_comments = list(result.scalars().all())
        
        # Build comment dictionary for easy lookup
        comment_dict = {comment.id: comment for comment in all_comments}
        
        # Separate parent comments and replies
        parent_comments = [c for c in all_comments if c.parent_comment_id is None]
        
        # Build nested structure
        structured_comments = []
        for parent in parent_comments:
            parent_data = {
                "id": parent.id,
                "tracker_id": parent.tracker_id,
                "user_id": parent.user_id,
                "username": parent.user.username if parent.user else "Unknown",
                "parent_comment_id": parent.parent_comment_id,
                "comment_text": parent.comment_text,
                "comment_type": parent.comment_type or "programming",
                "is_resolved": parent.is_resolved,
                "resolved_by_user_id": parent.resolved_by_user_id,
                "resolved_by_username": parent.resolved_by_user.username if parent.resolved_by_user else None,
                "resolved_at": parent.resolved_at,
                "created_at": parent.created_at,
                "updated_at": parent.updated_at,
                "is_parent_comment": True,
                "replies": []
            }
            
            # Find and add replies recursively
            def add_replies(comment_id: int, replies_list: List[Dict[str, Any]]):
                for comment in all_comments:
                    if comment.parent_comment_id == comment_id:
                        reply_data = {
                            "id": comment.id,
                            "tracker_id": comment.tracker_id,
                            "user_id": comment.user_id,
                            "username": comment.user.username if comment.user else "Unknown",
                            "parent_comment_id": comment.parent_comment_id,
                            "comment_text": comment.comment_text,
                            "comment_type": comment.comment_type or "programming",
                            "is_resolved": comment.is_resolved,
                            "resolved_by_user_id": comment.resolved_by_user_id,
                            "resolved_by_username": comment.resolved_by_user.username if comment.resolved_by_user else None,
                            "resolved_at": comment.resolved_at,
                            "created_at": comment.created_at,
                            "updated_at": comment.updated_at,
                            "is_parent_comment": False,
                            "replies": []
                        }
                        replies_list.append(reply_data)
                        # Recursively add nested replies
                        add_replies(comment.id, reply_data["replies"])
            
            add_replies(parent.id, parent_data["replies"])
            structured_comments.append(parent_data)
        
        return structured_comments

    async def get(self, db: AsyncSession, *, id: int) -> Optional[TrackerComment]:
        """Get a single comment by ID with relationships loaded."""
        query = select(TrackerComment).options(
            selectinload(TrackerComment.user),
            selectinload(TrackerComment.resolved_by_user)
        ).where(TrackerComment.id == id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update_comment_text(
        self,
        db: AsyncSession,
        *,
        comment_id: int,
        new_text: str
    ) -> Optional[TrackerComment]:
        """Update comment text (for editing functionality)."""
        try:
            comment = await self.get(db, id=comment_id)
            if not comment:
                return None
            
            comment.comment_text = new_text
            comment.updated_at = func.now()
            
            db.add(comment)
            await db.commit()
            await db.refresh(comment)
            return comment
            
        except Exception as e:
            await db.rollback()
            raise e

    async def unresolve_comment(
        self,
        db: AsyncSession,
        *,
        comment_id: int
    ) -> Optional[TrackerComment]:
        """
        Unresolve a parent comment and update tracker count.
        """
        try:
            comment = await self.get(db, id=comment_id)
            if not comment:
                return None
            
            # Only allow unresolving parent comments that are currently resolved
            if comment.parent_comment_id is not None:
                raise ValueError("Only parent comments can be unresolved")
            
            if not comment.is_resolved:
                return comment  # Already unresolved
            
            # Update comment
            comment.is_resolved = False
            comment.resolved_by_user_id = None
            comment.resolved_at = None
            
            # Update tracker count
            tracker = await db.execute(
                select(ReportingEffortItemTracker)
                .where(ReportingEffortItemTracker.id == comment.tracker_id)
            )
            tracker_obj = tracker.scalar_one_or_none()
            
            if tracker_obj:
                tracker_obj.unresolved_comment_count = tracker_obj.unresolved_comment_count + 1
                db.add(tracker_obj)
            
            db.add(comment)
            await db.commit()
            await db.refresh(comment)
            return comment
            
        except Exception as e:
            await db.rollback()
            raise e

    async def delete_comment(
        self,
        db: AsyncSession,
        *,
        comment_id: int
    ) -> Optional[TrackerComment]:
        """
        Delete a comment and update tracker count if it was an unresolved parent comment.
        Note: This will cascade delete all replies due to the relationship configuration.
        """
        try:
            comment = await self.get(db, id=comment_id)
            if not comment:
                return None
            
            # If deleting an unresolved parent comment, update tracker count
            was_unresolved_parent = (
                comment.parent_comment_id is None and 
                not comment.is_resolved
            )
            
            if was_unresolved_parent:
                tracker = await db.execute(
                    select(ReportingEffortItemTracker)
                    .where(ReportingEffortItemTracker.id == comment.tracker_id)
                )
                tracker_obj = tracker.scalar_one_or_none()
                
                if tracker_obj and tracker_obj.unresolved_comment_count > 0:
                    tracker_obj.unresolved_comment_count = tracker_obj.unresolved_comment_count - 1
                    db.add(tracker_obj)
            
            await db.delete(comment)
            await db.commit()
            return comment
            
        except Exception as e:
            await db.rollback()
            raise e

    async def get_comment_summary(
        self, 
        db: AsyncSession, 
        *, 
        tracker_id: int
    ) -> Dict[str, Any]:
        """
        Get comment summary with separate counts for programming and biostat comments.
        Only counts unresolved parent comments for badges.
        """
        # Get total count
        total_result = await db.execute(
            select(func.count(TrackerComment.id))
            .where(TrackerComment.tracker_id == tracker_id)
        )
        total_comments = total_result.scalar() or 0
        
        # Get unresolved parent comments count (total)
        unresolved_result = await db.execute(
            select(func.count(TrackerComment.id))
            .where(
                and_(
                    TrackerComment.tracker_id == tracker_id,
                    TrackerComment.parent_comment_id.is_(None),
                    TrackerComment.is_resolved == False
                )
            )
        )
        unresolved_count = unresolved_result.scalar() or 0
        
        # Get unresolved programming comments count
        prog_unresolved_result = await db.execute(
            select(func.count(TrackerComment.id))
            .where(
                and_(
                    TrackerComment.tracker_id == tracker_id,
                    TrackerComment.parent_comment_id.is_(None),
                    TrackerComment.is_resolved == False,
                    TrackerComment.comment_type == "programming"
                )
            )
        )
        programming_unresolved_count = prog_unresolved_result.scalar() or 0
        
        # Get unresolved biostat comments count
        biostat_unresolved_result = await db.execute(
            select(func.count(TrackerComment.id))
            .where(
                and_(
                    TrackerComment.tracker_id == tracker_id,
                    TrackerComment.parent_comment_id.is_(None),
                    TrackerComment.is_resolved == False,
                    TrackerComment.comment_type == "biostat"
                )
            )
        )
        biostat_unresolved_count = biostat_unresolved_result.scalar() or 0
        
        # Get resolved parent comments count
        resolved_result = await db.execute(
            select(func.count(TrackerComment.id))
            .where(
                and_(
                    TrackerComment.tracker_id == tracker_id,
                    TrackerComment.parent_comment_id.is_(None),
                    TrackerComment.is_resolved == True
                )
            )
        )
        resolved_parent_comments = resolved_result.scalar() or 0
        
        # Get total replies count
        replies_result = await db.execute(
            select(func.count(TrackerComment.id))
            .where(
                and_(
                    TrackerComment.tracker_id == tracker_id,
                    TrackerComment.parent_comment_id.isnot(None)
                )
            )
        )
        total_replies = replies_result.scalar() or 0
        
        # Get latest comment timestamp
        latest_result = await db.execute(
            select(func.max(TrackerComment.created_at))
            .where(TrackerComment.tracker_id == tracker_id)
        )
        latest_comment_at = latest_result.scalar()
        
        return {
            "tracker_id": tracker_id,
            "total_comments": total_comments,
            "unresolved_count": unresolved_count,
            "programming_unresolved_count": programming_unresolved_count,
            "biostat_unresolved_count": biostat_unresolved_count,
            "resolved_parent_comments": resolved_parent_comments,
            "total_replies": total_replies,
            "latest_comment_at": latest_comment_at
        }


# Create singleton instance
tracker_comment = TrackerCommentCRUD()