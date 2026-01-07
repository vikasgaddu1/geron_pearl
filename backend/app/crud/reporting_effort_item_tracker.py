"""CRUD operations for ReportingEffortItemTracker."""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
from app.models.milestone_tracker_assignment import MilestoneTrackerAssignment
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
        """Get multiple trackers with item details and full hierarchy."""
        from app.models.reporting_effort_item import ReportingEffortItem
        from app.models.reporting_effort import ReportingEffort
        from app.models.reporting_effort_tlf_details import ReportingEffortTlfDetails
        from app.models.reporting_effort_dataset_details import ReportingEffortDatasetDetails
        
        result = await db.execute(
            select(ReportingEffortItemTracker)
            .options(
                selectinload(ReportingEffortItemTracker.item)
                .selectinload(ReportingEffortItem.reporting_effort)
                .selectinload(ReportingEffort.study)
            )
            .options(
                selectinload(ReportingEffortItemTracker.item)
                .selectinload(ReportingEffortItem.reporting_effort)
                .selectinload(ReportingEffort.database_release)
            )
            # Load TLF details with title for TLF items
            .options(
                selectinload(ReportingEffortItemTracker.item)
                .selectinload(ReportingEffortItem.tlf_details)
                .selectinload(ReportingEffortTlfDetails.title)
            )
            # Load dataset details for SDTM/ADaM items
            .options(
                selectinload(ReportingEffortItemTracker.item)
                .selectinload(ReportingEffortItem.dataset_details)
            )
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
        """Get all trackers assigned to a specific programmer with full hierarchy."""
        from app.models.reporting_effort_item import ReportingEffortItem
        from app.models.reporting_effort import ReportingEffort

        if role == "production":
            filter_clause = ReportingEffortItemTracker.production_programmer_id == user_id
        else:
            filter_clause = ReportingEffortItemTracker.qc_programmer_id == user_id

        # Eager load item with full hierarchy
        result = await db.execute(
            select(ReportingEffortItemTracker)
            .options(
                selectinload(ReportingEffortItemTracker.item)
                .selectinload(ReportingEffortItem.reporting_effort)
                .selectinload(ReportingEffort.database_release),
                selectinload(ReportingEffortItemTracker.item)
                .selectinload(ReportingEffortItem.reporting_effort)
                .selectinload(ReportingEffort.study)
            )
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
        """Get trackers by status with item details and full hierarchy."""
        from app.models.reporting_effort_item import ReportingEffortItem
        from app.models.reporting_effort import ReportingEffort
        
        query = (
            select(ReportingEffortItemTracker)
            .options(
                selectinload(ReportingEffortItemTracker.item)
                .selectinload(ReportingEffortItem.reporting_effort)
                .selectinload(ReportingEffort.study)
            )
            .options(
                selectinload(ReportingEffortItemTracker.item)
                .selectinload(ReportingEffortItem.reporting_effort)
                .selectinload(ReportingEffort.database_release)
            )
        )

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
        obj_in: Union[ReportingEffortItemTrackerUpdate, Dict[str, Any]]
    ) -> ReportingEffortItemTracker:
        """Update a tracker entry."""
        # Handle both Pydantic models and dicts
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=True)
        
        # Check if production_status is changing to 'completed' for auto-recording
        old_status = db_obj.production_status
        new_status = update_data.get('production_status')
        should_record_completion = (
            new_status == 'completed' and 
            old_status != 'completed'
        )
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        # Update timestamp
        db_obj.updated_at = datetime.utcnow()
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Auto-record completion if status changed to 'completed'
        if should_record_completion:
            await self._record_completion(db, tracker=db_obj)
        
        return db_obj
    
    async def _record_completion(
        self,
        db: AsyncSession,
        *,
        tracker: ReportingEffortItemTracker
    ) -> None:
        """
        Record a completion event when tracker status becomes 'completed'.
        
        This captures a snapshot of the item and programmer context for velocity calculations.
        """
        from app.crud.item_completion_record import item_completion_record
        from app.models.reporting_effort_item import ReportingEffortItem
        from app.models.reporting_effort import ReportingEffort
        from app.models.study_team_assignment import StudyTeamAssignment
        
        # Check if completion already recorded (prevent duplicates)
        already_recorded = await item_completion_record.check_completion_exists(
            db, tracker_id=tracker.id
        )
        if already_recorded:
            return
        
        # Get item details
        item_result = await db.execute(
            select(ReportingEffortItem)
            .where(ReportingEffortItem.id == tracker.reporting_effort_item_id)
        )
        item = item_result.scalar_one_or_none()
        if not item:
            return
        
        # Get study_id from reporting effort
        effort_result = await db.execute(
            select(ReportingEffort)
            .where(ReportingEffort.id == item.reporting_effort_id)
        )
        effort = effort_result.scalar_one_or_none()
        if not effort:
            return
        
        study_id = effort.study_id
        
        # Get programmer allocation details if available
        programmer_experience = None
        programmer_allocation = None
        
        if tracker.production_programmer_id:
            assignment_result = await db.execute(
                select(StudyTeamAssignment)
                .where(
                    and_(
                        StudyTeamAssignment.user_id == tracker.production_programmer_id,
                        StudyTeamAssignment.study_id == study_id,
                        StudyTeamAssignment.is_active == True
                    )
                )
            )
            assignment = assignment_result.scalar_one_or_none()
            if assignment:
                programmer_experience = assignment.experience_level
                programmer_allocation = assignment.allocation_percentage
        
        # Check for sister study
        from app.models.study_sister_relation import StudySisterRelation
        sister_result = await db.execute(
            select(StudySisterRelation)
            .where(StudySisterRelation.primary_study_id == study_id)
            .limit(1)
        )
        sister_relation = sister_result.scalar_one_or_none()
        
        # Record the completion
        await item_completion_record.record_completion(
            db,
            tracker_id=tracker.id,
            study_id=study_id,
            item_type=item.item_type.value if hasattr(item.item_type, 'value') else str(item.item_type),
            item_subtype=item.item_subtype,
            item_code=item.item_code,
            complexity=tracker.complexity,
            production_programmer_id=tracker.production_programmer_id,
            programmer_experience_level=programmer_experience,
            programmer_allocation_percent=programmer_allocation,
            had_sister_study=sister_relation is not None,
            sister_study_id=sister_relation.sister_study_id if sister_relation else None
        )
    
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

    async def get_trackers_by_effort_bulk(
        self,
        db: AsyncSession,
        *,
        reporting_effort_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all trackers for a reporting effort with item and programmer details.
        Optimized to minimize N+1 queries by joining related data.
        Includes TLF title from text_elements for TLF items.
        Includes dataset label for SDTM/ADaM items.
        """
        from app.models.reporting_effort_item import ReportingEffortItem
        from app.models.reporting_effort_tlf_details import ReportingEffortTlfDetails
        from app.models.reporting_effort_dataset_details import ReportingEffortDatasetDetails
        from app.models.text_element import TextElement
        from app.models.user import User
        from sqlalchemy.orm import aliased
        
        # Create aliases for users to handle production and QC programmers
        prod_user = aliased(User)
        qc_user = aliased(User)
        # Alias for title text element
        title_element = aliased(TextElement)
        
        # Single query to get all trackers with related data including TLF title and dataset label
        query = select(
            ReportingEffortItemTracker,
            ReportingEffortItem.id.label('item_id'),
            ReportingEffortItem.item_code.label('item_code'),
            ReportingEffortItem.item_type.label('item_type'),
            ReportingEffortItem.item_subtype.label('item_subtype'),
            prod_user.username.label('prod_programmer_username'),
            qc_user.username.label('qc_programmer_username'),
            title_element.label.label('item_title'),
            ReportingEffortDatasetDetails.label.label('dataset_label')
        ).select_from(
            ReportingEffortItemTracker
        ).join(
            ReportingEffortItem,
            ReportingEffortItemTracker.reporting_effort_item_id == ReportingEffortItem.id
        ).outerjoin(
            prod_user,
            ReportingEffortItemTracker.production_programmer_id == prod_user.id
        ).outerjoin(
            qc_user,  
            ReportingEffortItemTracker.qc_programmer_id == qc_user.id
        ).outerjoin(
            ReportingEffortTlfDetails,
            ReportingEffortItem.id == ReportingEffortTlfDetails.reporting_effort_item_id
        ).outerjoin(
            title_element,
            ReportingEffortTlfDetails.title_id == title_element.id
        ).outerjoin(
            ReportingEffortDatasetDetails,
            ReportingEffortItem.id == ReportingEffortDatasetDetails.reporting_effort_item_id
        ).where(
            ReportingEffortItem.reporting_effort_id == reporting_effort_id
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        # Get all tracker IDs for bulk tag loading
        tracker_ids = [row.ReportingEffortItemTracker.id for row in rows]
        
        # Fetch tags for all trackers in one query
        from app.models.tracker_tag import TrackerTag, TrackerItemTag
        tags_by_tracker: Dict[int, List[Dict[str, Any]]] = {tid: [] for tid in tracker_ids}
        
        if tracker_ids:
            tag_result = await db.execute(
                select(TrackerItemTag, TrackerTag)
                .join(TrackerTag, TrackerItemTag.tag_id == TrackerTag.id)
                .where(TrackerItemTag.tracker_id.in_(tracker_ids))
                .order_by(TrackerItemTag.tracker_id, TrackerTag.name)
            )
            tag_rows = tag_result.all()
            
            for tag_row in tag_rows:
                tracker_id = tag_row.TrackerItemTag.tracker_id
                tag_dict = {
                    'id': tag_row.TrackerTag.id,
                    'name': tag_row.TrackerTag.name,
                    'color': tag_row.TrackerTag.color
                }
                tags_by_tracker[tracker_id].append(tag_dict)
        
        # Get milestone info for all trackers in bulk
        milestones_by_tracker = await self._get_milestones_for_trackers_bulk(
            db,
            tracker_ids=tracker_ids,
            reporting_effort_id=reporting_effort_id
        )

        # Convert to list of dictionaries with combined data
        trackers = []
        for row in rows:
            tracker_id = row.ReportingEffortItemTracker.id
            tracker_dict = {
                'id': tracker_id,
                'reporting_effort_item_id': row.ReportingEffortItemTracker.reporting_effort_item_id,
                'production_status': row.ReportingEffortItemTracker.production_status,
                'qc_status': row.ReportingEffortItemTracker.qc_status,
                'priority': row.ReportingEffortItemTracker.priority,
                'qc_level': row.ReportingEffortItemTracker.qc_level,
                'due_date': row.ReportingEffortItemTracker.due_date,
                'qc_completion_date': row.ReportingEffortItemTracker.qc_completion_date,
                'production_programmer_id': row.ReportingEffortItemTracker.production_programmer_id,
                'qc_programmer_id': row.ReportingEffortItemTracker.qc_programmer_id,
                'unresolved_comment_count': row.ReportingEffortItemTracker.unresolved_comment_count,
                'in_production_flag': row.ReportingEffortItemTracker.in_production_flag,  # Include production flag
                'created_at': row.ReportingEffortItemTracker.created_at,
                'updated_at': row.ReportingEffortItemTracker.updated_at,
                # Item details
                'item_id': row.item_id,
                'item_code': row.item_code,
                'item_type': row.item_type,
                'item_subtype': row.item_subtype,
                # Use TLF title for TLF items, dataset label for SDTM/ADaM items
                'item_title': row.item_title or row.dataset_label,
                'dataset_label': row.dataset_label,  # Also include separately for explicit access
                # Programmer usernames
                'prod_programmer_username': row.prod_programmer_username,
                'qc_programmer_username': row.qc_programmer_username,
                # Tags
                'tags': tags_by_tracker.get(tracker_id, []),
                # Milestones
                'milestones': milestones_by_tracker.get(tracker_id, [])
            }
            trackers.append(tracker_dict)

        return trackers

    async def _get_milestones_for_trackers_bulk(
        self,
        db: AsyncSession,
        *,
        tracker_ids: List[int],
        reporting_effort_id: int
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Get milestone info for multiple trackers efficiently.

        Returns: Dict mapping tracker_id -> list of milestone info
        """
        from app.models.reporting_effort_item import ReportingEffortItem
        from app.models.reporting_effort_milestone import ReportingEffortMilestone
        from app.models.reporting_effort_phase import ReportingEffortPhase
        from app.models.tracker_tag import TrackerItemTag

        if not tracker_ids:
            return {}

        # Initialize result
        result: Dict[int, List[Dict[str, Any]]] = {tid: [] for tid in tracker_ids}

        # Get tracker info (subtype, due_date)
        tracker_result = await db.execute(
            select(
                ReportingEffortItemTracker.id,
                ReportingEffortItemTracker.due_date,
                ReportingEffortItem.item_subtype
            )
            .join(ReportingEffortItem, ReportingEffortItemTracker.reporting_effort_item_id == ReportingEffortItem.id)
            .where(ReportingEffortItemTracker.id.in_(tracker_ids))
        )
        tracker_info = {r.id: {'due_date': r.due_date, 'item_subtype': r.item_subtype} for r in tracker_result.all()}

        # Get tags for all trackers
        tag_result = await db.execute(
            select(TrackerItemTag.tracker_id, TrackerItemTag.tag_id)
            .where(TrackerItemTag.tracker_id.in_(tracker_ids))
        )
        tracker_tags: Dict[int, set] = {tid: set() for tid in tracker_ids}
        for r in tag_result.all():
            tracker_tags[r.tracker_id].add(r.tag_id)

        # Get all milestones for this reporting effort
        milestone_result = await db.execute(
            select(ReportingEffortMilestone)
            .join(ReportingEffortPhase, ReportingEffortMilestone.phase_id == ReportingEffortPhase.id)
            .where(ReportingEffortPhase.reporting_effort_id == reporting_effort_id)
        )
        milestones = list(milestone_result.scalars().all())

        # Get manual assignments
        manual_result = await db.execute(
            select(MilestoneTrackerAssignment)
            .where(MilestoneTrackerAssignment.tracker_id.in_(tracker_ids))
        )
        manual_assignments: Dict[int, set] = {tid: set() for tid in tracker_ids}
        for ma in manual_result.scalars().all():
            manual_assignments[ma.tracker_id].add(ma.milestone_id)

        # Build milestone info for each tracker
        for tracker_id in tracker_ids:
            info = tracker_info.get(tracker_id)
            if not info:
                continue

            tracker_due_date = info['due_date']
            item_subtype = info['item_subtype']
            tags = tracker_tags[tracker_id]
            manuals = manual_assignments[tracker_id]

            for milestone in milestones:
                link_type = None

                # Check subtype link
                if milestone.linked_subtype and milestone.linked_subtype == item_subtype:
                    link_type = 'subtype'
                # Check tag link
                elif milestone.linked_tag_id and milestone.linked_tag_id in tags:
                    link_type = 'tag'
                # Check manual link
                elif milestone.id in manuals:
                    link_type = 'manual'

                if link_type:
                    is_past_due = False
                    if tracker_due_date and milestone.due_date:
                        is_past_due = tracker_due_date > milestone.due_date

                    result[tracker_id].append({
                        'milestone_id': milestone.id,
                        'milestone_name': milestone.name,
                        'milestone_due_date': milestone.due_date,
                        'is_past_due': is_past_due,
                        'link_type': link_type
                    })

        return result


# Create singleton instance
reporting_effort_item_tracker = ReportingEffortItemTrackerCRUD()