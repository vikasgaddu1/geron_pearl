"""CRUD operations for ReportingEffortItemTracker."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
from app.schemas.reporting_effort_item_tracker import (
    ReportingEffortItemTrackerCreate,
    ReportingEffortItemTrackerUpdate
)


class ReportingEffortItemTrackerCRUD:
    """CRUD operations for ReportingEffortItemTracker."""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: ReportingEffortItemTrackerCreate
    ) -> ReportingEffortItemTracker:
        """Create a new tracker entry."""
        db_obj = ReportingEffortItemTracker(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[ReportingEffortItemTracker]:
        """Get a single tracker by ID."""
        result = await db.execute(
            select(ReportingEffortItemTracker)
            .where(ReportingEffortItemTracker.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_item(
        self,
        db: AsyncSession,
        *,
        reporting_effort_item_id: int
    ) -> Optional[ReportingEffortItemTracker]:
        """Get tracker for a specific item."""
        result = await db.execute(
            select(ReportingEffortItemTracker)
            .where(ReportingEffortItemTracker.reporting_effort_item_id == reporting_effort_item_id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReportingEffortItemTracker]:
        """Get multiple trackers."""
        result = await db.execute(
            select(ReportingEffortItemTracker)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_programmer(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        role: str = "production"  # "production" or "qc"
    ) -> List[ReportingEffortItemTracker]:
        """Get all trackers assigned to a specific programmer."""
        if role == "production":
            filter_clause = ReportingEffortItemTracker.production_programmer_id == user_id
        else:
            filter_clause = ReportingEffortItemTracker.qc_programmer_id == user_id
        
        result = await db.execute(
            select(ReportingEffortItemTracker)
            .where(filter_clause)
            .order_by(ReportingEffortItemTracker.priority, ReportingEffortItemTracker.due_date)
        )
        return list(result.scalars().all())
    
    async def get_by_status(
        self,
        db: AsyncSession,
        *,
        production_status: Optional[str] = None,
        qc_status: Optional[str] = None
    ) -> List[ReportingEffortItemTracker]:
        """Get trackers by status."""
        query = select(ReportingEffortItemTracker)
        
        filters = []
        if production_status:
            filters.append(ReportingEffortItemTracker.production_status == production_status)
        if qc_status:
            filters.append(ReportingEffortItemTracker.qc_status == qc_status)
        
        if filters:
            query = query.where(and_(*filters))
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ReportingEffortItemTracker,
        obj_in: ReportingEffortItemTrackerUpdate
    ) -> ReportingEffortItemTracker:
        """Update a tracker entry."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # Update timestamp
        db_obj.updated_at = datetime.utcnow()
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def bulk_update(
        self,
        db: AsyncSession,
        *,
        updates: List[Dict[str, Any]]
    ) -> List[ReportingEffortItemTracker]:
        """
        Bulk update multiple trackers.
        
        Args:
            db: Database session
            updates: List of dicts with 'id' and fields to update
        
        Returns:
            List of updated trackers
        """
        updated_trackers = []
        
        for update_data in updates:
            tracker_id = update_data.pop('id')
            tracker = await self.get(db, id=tracker_id)
            
            if tracker:
                for field, value in update_data.items():
                    setattr(tracker, field, value)
                tracker.updated_at = datetime.utcnow()
                db.add(tracker)
                updated_trackers.append(tracker)
        
        if updated_trackers:
            await db.commit()
            for tracker in updated_trackers:
                await db.refresh(tracker)
        
        return updated_trackers
    
    async def delete(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[ReportingEffortItemTracker]:
        """Delete a tracker entry."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
        return db_obj
    
    async def get_workload_summary(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get workload summary for a user or all users.
        
        Returns:
            Dictionary with workload statistics
        """
        # Base query
        query = select(
            ReportingEffortItemTracker.production_programmer_id,
            ReportingEffortItemTracker.qc_programmer_id,
            func.count(ReportingEffortItemTracker.id).label("total_items"),
            func.sum(
                func.cast(
                    ReportingEffortItemTracker.production_status == "in_progress",
                    type_=int
                )
            ).label("in_progress_count"),
            func.sum(
                func.cast(
                    ReportingEffortItemTracker.production_status == "completed",
                    type_=int
                )
            ).label("completed_count")
        )
        
        if user_id:
            query = query.where(
                or_(
                    ReportingEffortItemTracker.production_programmer_id == user_id,
                    ReportingEffortItemTracker.qc_programmer_id == user_id
                )
            )
        
        query = query.group_by(
            ReportingEffortItemTracker.production_programmer_id,
            ReportingEffortItemTracker.qc_programmer_id
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        summary = {
            "total_items": sum(row.total_items for row in rows),
            "in_progress": sum(row.in_progress_count or 0 for row in rows),
            "completed": sum(row.completed_count or 0 for row in rows),
            "by_programmer": [
                {
                    "production_programmer_id": row.production_programmer_id,
                    "qc_programmer_id": row.qc_programmer_id,
                    "total": row.total_items,
                    "in_progress": row.in_progress_count or 0,
                    "completed": row.completed_count or 0
                }
                for row in rows
            ]
        }
        
        return summary


# Create singleton instance
reporting_effort_item_tracker = ReportingEffortItemTrackerCRUD()