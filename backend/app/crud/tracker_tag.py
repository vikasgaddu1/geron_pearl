"""CRUD operations for Tracker Tags."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tracker_tag import TrackerTag, TrackerItemTag
from app.schemas.tracker_tag import (
    TrackerTagCreate, TrackerTagUpdate,
    TrackerItemTagCreate, BulkOperationResult
)


class TrackerTagCRUD:
    """CRUD operations for TrackerTag."""
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: TrackerTagCreate
    ) -> TrackerTag:
        """Create a new tag."""
        db_obj = TrackerTag(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> Optional[TrackerTag]:
        """Get a single tag by ID."""
        result = await db.execute(
            select(TrackerTag).where(TrackerTag.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(
        self,
        db: AsyncSession,
        *,
        name: str
    ) -> Optional[TrackerTag]:
        """Get a tag by name."""
        result = await db.execute(
            select(TrackerTag).where(TrackerTag.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TrackerTag]:
        """Get all tags."""
        result = await db.execute(
            select(TrackerTag)
            .order_by(TrackerTag.name)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_all_with_counts(
        self,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Get all tags with usage counts."""
        # Query tags with count of associated trackers
        query = select(
            TrackerTag,
            func.count(TrackerItemTag.id).label('usage_count')
        ).outerjoin(
            TrackerItemTag,
            TrackerTag.id == TrackerItemTag.tag_id
        ).group_by(TrackerTag.id).order_by(TrackerTag.name)
        
        result = await db.execute(query)
        rows = result.all()
        
        tags = []
        for row in rows:
            tag_dict = {
                'id': row.TrackerTag.id,
                'name': row.TrackerTag.name,
                'color': row.TrackerTag.color,
                'description': row.TrackerTag.description,
                'created_at': row.TrackerTag.created_at,
                'updated_at': row.TrackerTag.updated_at,
                'usage_count': row.usage_count or 0
            }
            tags.append(tag_dict)
        
        return tags
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: TrackerTag,
        obj_in: TrackerTagUpdate
    ) -> TrackerTag:
        """Update a tag."""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(
        self,
        db: AsyncSession,
        *,
        id: int
    ) -> bool:
        """Delete a tag. Returns True if deleted, False if not found."""
        db_obj = await self.get(db, id=id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return True
        return False


class TrackerItemTagCRUD:
    """CRUD operations for TrackerItemTag (tracker-tag associations)."""
    
    async def assign_tag(
        self,
        db: AsyncSession,
        *,
        tracker_id: int,
        tag_id: int
    ) -> Optional[TrackerItemTag]:
        """Assign a tag to a tracker. Returns None if already assigned."""
        # Check if already assigned
        existing = await self.get_assignment(db, tracker_id=tracker_id, tag_id=tag_id)
        if existing:
            return existing
        
        db_obj = TrackerItemTag(tracker_id=tracker_id, tag_id=tag_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def remove_tag(
        self,
        db: AsyncSession,
        *,
        tracker_id: int,
        tag_id: int
    ) -> bool:
        """Remove a tag from a tracker. Returns True if removed."""
        result = await db.execute(
            delete(TrackerItemTag).where(
                TrackerItemTag.tracker_id == tracker_id,
                TrackerItemTag.tag_id == tag_id
            )
        )
        await db.commit()
        return result.rowcount > 0
    
    async def get_assignment(
        self,
        db: AsyncSession,
        *,
        tracker_id: int,
        tag_id: int
    ) -> Optional[TrackerItemTag]:
        """Get a specific tag assignment."""
        result = await db.execute(
            select(TrackerItemTag).where(
                TrackerItemTag.tracker_id == tracker_id,
                TrackerItemTag.tag_id == tag_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_tags_for_tracker(
        self,
        db: AsyncSession,
        *,
        tracker_id: int
    ) -> List[TrackerTag]:
        """Get all tags assigned to a tracker."""
        result = await db.execute(
            select(TrackerTag)
            .join(TrackerItemTag, TrackerTag.id == TrackerItemTag.tag_id)
            .where(TrackerItemTag.tracker_id == tracker_id)
            .order_by(TrackerTag.name)
        )
        return list(result.scalars().all())
    
    async def get_trackers_by_tag(
        self,
        db: AsyncSession,
        *,
        tag_id: int
    ) -> List[int]:
        """Get all tracker IDs that have a specific tag."""
        result = await db.execute(
            select(TrackerItemTag.tracker_id)
            .where(TrackerItemTag.tag_id == tag_id)
        )
        return [row[0] for row in result.all()]
    
    async def bulk_assign_tag(
        self,
        db: AsyncSession,
        *,
        tracker_ids: List[int],
        tag_id: int
    ) -> BulkOperationResult:
        """Assign a tag to multiple trackers."""
        affected = 0
        errors = []
        
        for tracker_id in tracker_ids:
            try:
                # Check if already assigned
                existing = await self.get_assignment(db, tracker_id=tracker_id, tag_id=tag_id)
                if not existing:
                    db_obj = TrackerItemTag(tracker_id=tracker_id, tag_id=tag_id)
                    db.add(db_obj)
                    affected += 1
            except Exception as e:
                errors.append(f"Failed to assign tag to tracker {tracker_id}: {str(e)}")
        
        if affected > 0:
            await db.commit()
        
        return BulkOperationResult(
            success=len(errors) == 0,
            affected_count=affected,
            errors=errors
        )
    
    async def bulk_remove_tag(
        self,
        db: AsyncSession,
        *,
        tracker_ids: List[int],
        tag_id: int
    ) -> BulkOperationResult:
        """Remove a tag from multiple trackers."""
        result = await db.execute(
            delete(TrackerItemTag).where(
                TrackerItemTag.tracker_id.in_(tracker_ids),
                TrackerItemTag.tag_id == tag_id
            )
        )
        await db.commit()
        
        return BulkOperationResult(
            success=True,
            affected_count=result.rowcount,
            errors=[]
        )
    
    async def get_tags_for_trackers_bulk(
        self,
        db: AsyncSession,
        *,
        tracker_ids: List[int]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Get all tags for multiple trackers at once (optimized for bulk loading)."""
        if not tracker_ids:
            return {}
        
        result = await db.execute(
            select(TrackerItemTag, TrackerTag)
            .join(TrackerTag, TrackerItemTag.tag_id == TrackerTag.id)
            .where(TrackerItemTag.tracker_id.in_(tracker_ids))
            .order_by(TrackerItemTag.tracker_id, TrackerTag.name)
        )
        rows = result.all()
        
        # Group by tracker_id
        tags_by_tracker: Dict[int, List[Dict[str, Any]]] = {tid: [] for tid in tracker_ids}
        for row in rows:
            tracker_id = row.TrackerItemTag.tracker_id
            tag_dict = {
                'id': row.TrackerTag.id,
                'name': row.TrackerTag.name,
                'color': row.TrackerTag.color
            }
            tags_by_tracker[tracker_id].append(tag_dict)
        
        return tags_by_tracker


# Create singleton instances
tracker_tag = TrackerTagCRUD()
tracker_item_tag = TrackerItemTagCRUD()

