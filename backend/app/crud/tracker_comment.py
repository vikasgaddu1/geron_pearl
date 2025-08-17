"""
CRUD operations for TrackerComment model
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import and_, desc, func, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.future import select

from app.models.tracker_comment import TrackerComment, CommentType
from app.models.user import User
from app.schemas.tracker_comment import (
    TrackerCommentCreate, 
    TrackerCommentUpdate,
    CommentFilter,
    CommentSummary
)


class TrackerCommentCRUD:
    """CRUD operations for tracker comments"""

    async def get(self, db: AsyncSession, *, id: int) -> Optional[TrackerComment]:
        """Get a comment by ID"""
        query = select(TrackerComment).options(
            selectinload(TrackerComment.user),
            selectinload(TrackerComment.resolved_by_user),
            selectinload(TrackerComment.replies).selectinload(TrackerComment.user)
        ).where(TrackerComment.id == id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: TrackerComment, 
        obj_in: TrackerCommentUpdate
    ) -> TrackerComment:
        """Update a comment"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[TrackerComment]:
        """Hard delete a comment"""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.flush()
        return db_obj

    async def create_with_user(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: TrackerCommentCreate, 
        user_id: int
    ) -> TrackerComment:
        """Create a comment with user association"""
        obj_data = obj_in.model_dump()
        obj_data["user_id"] = user_id
        
        db_obj = TrackerComment(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_tracker_id(
        self, 
        db: AsyncSession, 
        *, 
        tracker_id: int,
        include_deleted: bool = False
    ) -> List[TrackerComment]:
        """Get all comments for a specific tracker item"""
        query = select(TrackerComment).options(
            selectinload(TrackerComment.user),
            selectinload(TrackerComment.resolved_by_user),
            selectinload(TrackerComment.replies).selectinload(TrackerComment.user)
        ).where(TrackerComment.tracker_id == tracker_id)
        
        if not include_deleted:
            query = query.where(TrackerComment.is_deleted == False)
            
        # Order by pinned status (pinned first), then creation date (newest first)
        query = query.order_by(
            desc(TrackerComment.is_pinned),
            desc(TrackerComment.created_at)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_thread_comments(
        self, 
        db: AsyncSession, 
        *, 
        parent_comment_id: int
    ) -> List[TrackerComment]:
        """Get all replies in a comment thread"""
        query = select(TrackerComment).options(
            selectinload(TrackerComment.user),
            selectinload(TrackerComment.resolved_by_user)
        ).where(
            TrackerComment.parent_comment_id == parent_comment_id,
            TrackerComment.is_deleted == False
        ).order_by(TrackerComment.created_at)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_comments_summary(
        self, 
        db: AsyncSession, 
        *, 
        tracker_ids: List[int]
    ) -> Dict[int, CommentSummary]:
        """Get comment summaries for multiple tracker items"""
        if not tracker_ids:
            return {}
            
        # Build query for comment statistics
        query = select(
            TrackerComment.tracker_id,
            func.count(TrackerComment.id).label('total_comments'),
            func.sum(case((TrackerComment.is_resolved == False, 1), else_=0)).label('unresolved_comments'),
            func.sum(case((TrackerComment.is_pinned == True, 1), else_=0)).label('pinned_comments'),
            func.max(TrackerComment.created_at).label('last_comment_at')
        ).where(
            TrackerComment.tracker_id.in_(tracker_ids),
            TrackerComment.is_deleted == False
        ).group_by(TrackerComment.tracker_id)
        
        result = await db.execute(query)
        stats = {row.tracker_id: row for row in result.all()}
        
        # Get last comment details for each tracker
        last_comment_query = select(
            TrackerComment.tracker_id,
            TrackerComment.comment_type,
            User.username
        ).join(User, TrackerComment.user_id == User.id).where(
            TrackerComment.tracker_id.in_(tracker_ids),
            TrackerComment.is_deleted == False
        ).order_by(desc(TrackerComment.created_at)).limit(len(tracker_ids))
        
        last_result = await db.execute(last_comment_query)
        last_comments = {row.tracker_id: row for row in last_result.all()}
        
        # Build summary objects
        summaries = {}
        for tracker_id in tracker_ids:
            stat = stats.get(tracker_id)
            last = last_comments.get(tracker_id)
            
            summaries[tracker_id] = CommentSummary(
                tracker_id=tracker_id,
                total_comments=stat.total_comments if stat else 0,
                unresolved_comments=stat.unresolved_comments if stat else 0,
                pinned_comments=stat.pinned_comments if stat else 0,
                last_comment_at=stat.last_comment_at if stat else None,
                last_comment_type=last.comment_type if last else None,
                last_comment_user=last.username if last else None
            )
            
        return summaries

    async def mark_resolved(
        self, 
        db: AsyncSession, 
        *, 
        comment_id: int, 
        user_id: int,
        is_resolved: bool = True
    ) -> Optional[TrackerComment]:
        """Mark a comment as resolved or unresolved"""
        db_obj = await self.get(db, id=comment_id)
        if not db_obj:
            return None
            
        db_obj.is_resolved = is_resolved
        if is_resolved:
            db_obj.resolved_by_user_id = user_id
            db_obj.resolved_at = func.now()
        else:
            db_obj.resolved_by_user_id = None
            db_obj.resolved_at = None
            
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def toggle_pin(
        self, 
        db: AsyncSession, 
        *, 
        comment_id: int
    ) -> Optional[TrackerComment]:
        """Toggle pin status of a comment"""
        db_obj = await self.get(db, id=comment_id)
        if not db_obj:
            return None
            
        db_obj.is_pinned = not db_obj.is_pinned
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def soft_delete(
        self, 
        db: AsyncSession, 
        *, 
        comment_id: int
    ) -> Optional[TrackerComment]:
        """Soft delete a comment (mark as deleted)"""
        db_obj = await self.get(db, id=comment_id)
        if not db_obj:
            return None
            
        db_obj.is_deleted = True
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def search_comments(
        self, 
        db: AsyncSession, 
        *, 
        filter_params: CommentFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[TrackerComment]:
        """Search comments with filters"""
        query = select(TrackerComment).options(
            selectinload(TrackerComment.user),
            selectinload(TrackerComment.resolved_by_user)
        )
        
        # Apply filters
        conditions = [TrackerComment.is_deleted == False]
        
        if filter_params.tracker_ids:
            conditions.append(TrackerComment.tracker_id.in_(filter_params.tracker_ids))
            
        if filter_params.comment_types:
            conditions.append(TrackerComment.comment_type.in_(filter_params.comment_types))
            
        if filter_params.is_resolved is not None:
            conditions.append(TrackerComment.is_resolved == filter_params.is_resolved)
            
        if filter_params.is_pinned is not None:
            conditions.append(TrackerComment.is_pinned == filter_params.is_pinned)
            
        if filter_params.user_ids:
            conditions.append(TrackerComment.user_id.in_(filter_params.user_ids))
            
        if filter_params.date_from:
            conditions.append(TrackerComment.created_at >= filter_params.date_from)
            
        if filter_params.date_to:
            conditions.append(TrackerComment.created_at <= filter_params.date_to)
            
        if filter_params.search_text:
            search_term = f"%{filter_params.search_text}%"
            conditions.append(TrackerComment.comment_text.ilike(search_term))
        
        query = query.where(and_(*conditions))
        query = query.order_by(desc(TrackerComment.created_at))
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_user_stats(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int
    ) -> Dict[str, Any]:
        """Get comment statistics for a user"""
        query = select(
            func.count(TrackerComment.id).label('total_comments'),
            func.sum(case((TrackerComment.is_resolved == False, 1), else_=0)).label('unresolved_comments'),
            func.sum(case((TrackerComment.comment_type == CommentType.qc_comment, 1), else_=0)).label('qc_comments'),
            func.sum(case((TrackerComment.comment_type == CommentType.prod_comment, 1), else_=0)).label('prod_comments'),
            func.sum(case((TrackerComment.comment_type == CommentType.biostat_comment, 1), else_=0)).label('biostat_comments')
        ).where(
            TrackerComment.user_id == user_id,
            TrackerComment.is_deleted == False
        )
        
        result = await db.execute(query)
        row = result.first()
        
        return {
            'total_comments': row.total_comments or 0,
            'unresolved_comments': row.unresolved_comments or 0,
            'qc_comments': row.qc_comments or 0,
            'prod_comments': row.prod_comments or 0,
            'biostat_comments': row.biostat_comments or 0
        }


# Create instance
tracker_comment = TrackerCommentCRUD()