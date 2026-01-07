"""CRUD operations for ReportingEffortMilestone."""

from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.crud.base import BaseCRUD
from app.models.reporting_effort_milestone import ReportingEffortMilestone
from app.models.reporting_effort_phase import ReportingEffortPhase
from app.models.reporting_effort import ReportingEffort
from app.models.reporting_effort_item import ReportingEffortItem
from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
from app.models.milestone_tracker_assignment import MilestoneTrackerAssignment
from app.models.tracker_tag import TrackerTag, TrackerItemTag
from app.models.study import Study
from app.schemas.reporting_effort_milestone import (
    ReportingEffortMilestoneCreate,
    ReportingEffortMilestoneUpdate
)


class CRUDReportingEffortMilestone(BaseCRUD[ReportingEffortMilestone, ReportingEffortMilestoneCreate, ReportingEffortMilestoneUpdate]):
    """CRUD operations for ReportingEffortMilestone."""
    
    async def get_by_phase(
        self, 
        db: AsyncSession, 
        *, 
        phase_id: int
    ) -> List[ReportingEffortMilestone]:
        """Get all milestones for a phase, ordered by display_order."""
        result = await db.execute(
            select(ReportingEffortMilestone)
            .where(ReportingEffortMilestone.phase_id == phase_id)
            .order_by(ReportingEffortMilestone.display_order)
        )
        return list(result.scalars().all())
    
    async def get_next_display_order(
        self, 
        db: AsyncSession, 
        *, 
        phase_id: int
    ) -> int:
        """Get the next display order for a new milestone."""
        result = await db.execute(
            select(ReportingEffortMilestone.display_order)
            .where(ReportingEffortMilestone.phase_id == phase_id)
            .order_by(ReportingEffortMilestone.display_order.desc())
            .limit(1)
        )
        max_order = result.scalar_one_or_none()
        return (max_order or 0) + 1
    
    async def reorder_milestones(
        self, 
        db: AsyncSession, 
        *, 
        phase_id: int,
        milestone_ids: List[int]
    ) -> List[ReportingEffortMilestone]:
        """Reorder milestones by updating their display_order based on the given ID list."""
        milestones = await self.get_by_phase(db, phase_id=phase_id)
        milestone_map = {m.id: m for m in milestones}
        
        for order, milestone_id in enumerate(milestone_ids):
            if milestone_id in milestone_map:
                milestone_map[milestone_id].display_order = order
        
        await db.commit()
        return await self.get_by_phase(db, phase_id=phase_id)
    
    async def mark_completed(
        self, 
        db: AsyncSession, 
        *, 
        milestone_id: int,
        completion_date: Optional[date] = None
    ) -> Optional[ReportingEffortMilestone]:
        """Mark a milestone as completed."""
        milestone = await self.get(db, id=milestone_id)
        if milestone:
            milestone.is_completed = True
            milestone.completion_date = completion_date or date.today()
            await db.commit()
            await db.refresh(milestone)
        return milestone
    
    async def mark_incomplete(
        self, 
        db: AsyncSession, 
        *, 
        milestone_id: int
    ) -> Optional[ReportingEffortMilestone]:
        """Mark a milestone as incomplete."""
        milestone = await self.get(db, id=milestone_id)
        if milestone:
            milestone.is_completed = False
            milestone.completion_date = None
            await db.commit()
            await db.refresh(milestone)
        return milestone
    
    async def get_all_for_dashboard(
        self, 
        db: AsyncSession, 
        *,
        study_id: Optional[int] = None,
        reporting_effort_id: Optional[int] = None,
        include_completed: bool = True,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get all milestones with full context for dashboard display."""
        query = (
            select(
                ReportingEffortMilestone,
                ReportingEffortPhase.name.label('phase_name'),
                ReportingEffort.id.label('reporting_effort_id'),
                ReportingEffort.database_release_label.label('reporting_effort_label'),
                Study.id.label('study_id'),
                Study.study_label.label('study_label')
            )
            .join(ReportingEffortPhase, ReportingEffortMilestone.phase_id == ReportingEffortPhase.id)
            .join(ReportingEffort, ReportingEffortPhase.reporting_effort_id == ReportingEffort.id)
            .join(Study, ReportingEffort.study_id == Study.id)
        )
        
        # Apply filters
        conditions = []
        if study_id:
            conditions.append(Study.id == study_id)
        if reporting_effort_id:
            conditions.append(ReportingEffort.id == reporting_effort_id)
        if not include_completed:
            conditions.append(ReportingEffortMilestone.is_completed == False)
        if start_date:
            conditions.append(ReportingEffortMilestone.due_date >= start_date)
        if end_date:
            conditions.append(ReportingEffortMilestone.due_date <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(
            ReportingEffortMilestone.due_date,
            ReportingEffortPhase.display_order,
            ReportingEffortMilestone.display_order
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        # Convert to dict format with all context
        return [
            {
                'id': row.ReportingEffortMilestone.id,
                'phase_id': row.ReportingEffortMilestone.phase_id,
                'name': row.ReportingEffortMilestone.name,
                'start_date': row.ReportingEffortMilestone.start_date,
                'due_date': row.ReportingEffortMilestone.due_date,
                'responsibility': row.ReportingEffortMilestone.responsibility,
                'comments': row.ReportingEffortMilestone.comments,
                'is_completed': row.ReportingEffortMilestone.is_completed,
                'completion_date': row.ReportingEffortMilestone.completion_date,
                'display_order': row.ReportingEffortMilestone.display_order,
                'created_at': row.ReportingEffortMilestone.created_at,
                'updated_at': row.ReportingEffortMilestone.updated_at,
                'phase_name': row.phase_name,
                'reporting_effort_id': row.reporting_effort_id,
                'reporting_effort_label': row.reporting_effort_label,
                'study_id': row.study_id,
                'study_label': row.study_label
            }
            for row in rows
        ]
    
    async def get_upcoming(
        self, 
        db: AsyncSession, 
        *,
        days_ahead: int = 14,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get upcoming milestones within the specified number of days."""
        today = date.today()
        end_date = date.fromordinal(today.toordinal() + days_ahead)
        
        milestones = await self.get_all_for_dashboard(
            db,
            include_completed=False,
            start_date=today,
            end_date=end_date
        )
        
        return milestones[:limit]

    async def get_linked_trackers(
        self,
        db: AsyncSession,
        *,
        milestone_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all trackers linked to a milestone.

        A tracker is linked if ANY of these conditions is true:
        1. milestone.linked_subtype matches item.item_subtype
        2. milestone.linked_tag_id matches a tag assigned to the tracker
        3. A manual assignment exists in milestone_tracker_assignments

        Returns: List of tracker dicts with link_type indicator
        """
        milestone = await self.get(db, id=milestone_id)
        if not milestone:
            return []

        # Get the reporting effort ID for this milestone (via phase)
        phase_result = await db.execute(
            select(ReportingEffortPhase.reporting_effort_id)
            .where(ReportingEffortPhase.id == milestone.phase_id)
        )
        reporting_effort_id = phase_result.scalar_one_or_none()
        if not reporting_effort_id:
            return []

        linked_trackers: Dict[int, Dict[str, Any]] = {}

        # 1. Get trackers linked by subtype
        if milestone.linked_subtype:
            subtype_result = await db.execute(
                select(ReportingEffortItemTracker, ReportingEffortItem.item_code, ReportingEffortItem.item_subtype)
                .join(ReportingEffortItem, ReportingEffortItemTracker.reporting_effort_item_id == ReportingEffortItem.id)
                .where(
                    and_(
                        ReportingEffortItem.reporting_effort_id == reporting_effort_id,
                        ReportingEffortItem.item_subtype == milestone.linked_subtype
                    )
                )
            )
            for row in subtype_result.all():
                tracker = row.ReportingEffortItemTracker
                if tracker.id not in linked_trackers:
                    linked_trackers[tracker.id] = {
                        'id': tracker.id,
                        'item_code': row.item_code,
                        'item_subtype': row.item_subtype,
                        'due_date': tracker.due_date,
                        'link_type': 'subtype',
                        'is_past_due': self._is_past_due(tracker.due_date, milestone.due_date)
                    }

        # 2. Get trackers linked by tag
        if milestone.linked_tag_id:
            tag_result = await db.execute(
                select(ReportingEffortItemTracker, ReportingEffortItem.item_code, ReportingEffortItem.item_subtype)
                .join(ReportingEffortItem, ReportingEffortItemTracker.reporting_effort_item_id == ReportingEffortItem.id)
                .join(TrackerItemTag, TrackerItemTag.tracker_id == ReportingEffortItemTracker.id)
                .where(
                    and_(
                        ReportingEffortItem.reporting_effort_id == reporting_effort_id,
                        TrackerItemTag.tag_id == milestone.linked_tag_id
                    )
                )
            )
            for row in tag_result.all():
                tracker = row.ReportingEffortItemTracker
                if tracker.id not in linked_trackers:
                    linked_trackers[tracker.id] = {
                        'id': tracker.id,
                        'item_code': row.item_code,
                        'item_subtype': row.item_subtype,
                        'due_date': tracker.due_date,
                        'link_type': 'tag',
                        'is_past_due': self._is_past_due(tracker.due_date, milestone.due_date)
                    }

        # 3. Get manually assigned trackers
        manual_result = await db.execute(
            select(ReportingEffortItemTracker, ReportingEffortItem.item_code, ReportingEffortItem.item_subtype)
            .join(ReportingEffortItem, ReportingEffortItemTracker.reporting_effort_item_id == ReportingEffortItem.id)
            .join(MilestoneTrackerAssignment, MilestoneTrackerAssignment.tracker_id == ReportingEffortItemTracker.id)
            .where(
                and_(
                    ReportingEffortItem.reporting_effort_id == reporting_effort_id,
                    MilestoneTrackerAssignment.milestone_id == milestone_id
                )
            )
        )
        for row in manual_result.all():
            tracker = row.ReportingEffortItemTracker
            if tracker.id not in linked_trackers:
                linked_trackers[tracker.id] = {
                    'id': tracker.id,
                    'item_code': row.item_code,
                    'item_subtype': row.item_subtype,
                    'due_date': tracker.due_date,
                    'link_type': 'manual',
                    'is_past_due': self._is_past_due(tracker.due_date, milestone.due_date)
                }

        return list(linked_trackers.values())

    def _is_past_due(self, tracker_due_date: Optional[date], milestone_due_date: Optional[date]) -> bool:
        """Check if tracker due date is after milestone due date."""
        if not tracker_due_date or not milestone_due_date:
            return False
        return tracker_due_date > milestone_due_date

    async def get_milestone_with_tracker_info(
        self,
        db: AsyncSession,
        *,
        milestone_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a milestone with linked tracker information.

        Returns: Milestone dict with linked_tracker_count, trackers_past_due, linked_tag_name
        """
        # Get milestone with linked tag eagerly loaded
        result = await db.execute(
            select(ReportingEffortMilestone)
            .options(selectinload(ReportingEffortMilestone.linked_tag))
            .where(ReportingEffortMilestone.id == milestone_id)
        )
        milestone = result.scalar_one_or_none()
        if not milestone:
            return None

        # Get linked trackers
        linked_trackers = await self.get_linked_trackers(db, milestone_id=milestone_id)

        # Get manually assigned tracker IDs
        manual_result = await db.execute(
            select(MilestoneTrackerAssignment.tracker_id)
            .where(MilestoneTrackerAssignment.milestone_id == milestone_id)
        )
        manual_tracker_ids = [row[0] for row in manual_result.all()]

        return {
            'id': milestone.id,
            'phase_id': milestone.phase_id,
            'name': milestone.name,
            'start_date': milestone.start_date,
            'due_date': milestone.due_date,
            'responsibility': milestone.responsibility,
            'comments': milestone.comments,
            'is_completed': milestone.is_completed,
            'completion_date': milestone.completion_date,
            'display_order': milestone.display_order,
            'linked_subtype': milestone.linked_subtype,
            'linked_tag_id': milestone.linked_tag_id,
            'linked_tag_name': milestone.linked_tag.name if milestone.linked_tag else None,
            'linked_tracker_ids': manual_tracker_ids,
            'linked_tracker_count': len(linked_trackers),
            'trackers_past_due': sum(1 for t in linked_trackers if t['is_past_due']),
            'created_at': milestone.created_at,
            'updated_at': milestone.updated_at
        }

    async def get_available_trackers(
        self,
        db: AsyncSession,
        *,
        milestone_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get trackers that can be manually linked to this milestone.

        Returns trackers in the same reporting effort that are NOT already linked
        (by subtype, tag, or manual assignment).
        """
        milestone = await self.get(db, id=milestone_id)
        if not milestone:
            return []

        # Get linked tracker IDs
        linked_trackers = await self.get_linked_trackers(db, milestone_id=milestone_id)
        linked_ids = {t['id'] for t in linked_trackers}

        # Get the reporting effort ID
        phase_result = await db.execute(
            select(ReportingEffortPhase.reporting_effort_id)
            .where(ReportingEffortPhase.id == milestone.phase_id)
        )
        reporting_effort_id = phase_result.scalar_one_or_none()
        if not reporting_effort_id:
            return []

        # Get all trackers in the same reporting effort
        all_result = await db.execute(
            select(ReportingEffortItemTracker, ReportingEffortItem.item_code, ReportingEffortItem.item_subtype)
            .join(ReportingEffortItem, ReportingEffortItemTracker.reporting_effort_item_id == ReportingEffortItem.id)
            .where(ReportingEffortItem.reporting_effort_id == reporting_effort_id)
        )

        available = []
        for row in all_result.all():
            tracker = row.ReportingEffortItemTracker
            if tracker.id not in linked_ids:
                available.append({
                    'id': tracker.id,
                    'item_code': row.item_code,
                    'item_subtype': row.item_subtype,
                    'due_date': tracker.due_date
                })

        return available

    async def get_milestones_for_tracker(
        self,
        db: AsyncSession,
        *,
        tracker_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all milestones that a tracker is linked to.

        Returns: List of milestone info with link_type indicator
        """
        # Get tracker with item info
        tracker_result = await db.execute(
            select(ReportingEffortItemTracker, ReportingEffortItem.item_subtype, ReportingEffortItem.reporting_effort_id)
            .join(ReportingEffortItem, ReportingEffortItemTracker.reporting_effort_item_id == ReportingEffortItem.id)
            .where(ReportingEffortItemTracker.id == tracker_id)
        )
        row = tracker_result.first()
        if not row:
            return []

        tracker = row.ReportingEffortItemTracker
        item_subtype = row.item_subtype
        reporting_effort_id = row.reporting_effort_id

        # Get tracker's tags
        tag_result = await db.execute(
            select(TrackerItemTag.tag_id)
            .where(TrackerItemTag.tracker_id == tracker_id)
        )
        tracker_tag_ids = {r[0] for r in tag_result.all()}

        # Get milestones from the same reporting effort
        milestone_result = await db.execute(
            select(ReportingEffortMilestone, ReportingEffortPhase.name.label('phase_name'))
            .join(ReportingEffortPhase, ReportingEffortMilestone.phase_id == ReportingEffortPhase.id)
            .options(selectinload(ReportingEffortMilestone.linked_tag))
            .where(ReportingEffortPhase.reporting_effort_id == reporting_effort_id)
        )

        linked_milestones: Dict[int, Dict[str, Any]] = {}

        for m_row in milestone_result.all():
            milestone = m_row.ReportingEffortMilestone
            link_type = None

            # Check subtype link
            if milestone.linked_subtype and milestone.linked_subtype == item_subtype:
                link_type = 'subtype'
            # Check tag link
            elif milestone.linked_tag_id and milestone.linked_tag_id in tracker_tag_ids:
                link_type = 'tag'

            if link_type and milestone.id not in linked_milestones:
                linked_milestones[milestone.id] = {
                    'milestone_id': milestone.id,
                    'milestone_name': milestone.name,
                    'milestone_due_date': milestone.due_date,
                    'phase_name': m_row.phase_name,
                    'is_past_due': self._is_past_due(tracker.due_date, milestone.due_date),
                    'link_type': link_type
                }

        # Check manual assignments
        manual_result = await db.execute(
            select(MilestoneTrackerAssignment.milestone_id)
            .where(MilestoneTrackerAssignment.tracker_id == tracker_id)
        )
        manual_milestone_ids = [r[0] for r in manual_result.all()]

        if manual_milestone_ids:
            manual_milestone_result = await db.execute(
                select(ReportingEffortMilestone, ReportingEffortPhase.name.label('phase_name'))
                .join(ReportingEffortPhase, ReportingEffortMilestone.phase_id == ReportingEffortPhase.id)
                .where(ReportingEffortMilestone.id.in_(manual_milestone_ids))
            )
            for m_row in manual_milestone_result.all():
                milestone = m_row.ReportingEffortMilestone
                if milestone.id not in linked_milestones:
                    linked_milestones[milestone.id] = {
                        'milestone_id': milestone.id,
                        'milestone_name': milestone.name,
                        'milestone_due_date': milestone.due_date,
                        'phase_name': m_row.phase_name,
                        'is_past_due': self._is_past_due(tracker.due_date, milestone.due_date),
                        'link_type': 'manual'
                    }

        return list(linked_milestones.values())

    async def get_milestones_for_trackers_bulk(
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
            .options(selectinload(ReportingEffortMilestone.linked_tag))
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
                    result[tracker_id].append({
                        'milestone_id': milestone.id,
                        'milestone_name': milestone.name,
                        'milestone_due_date': milestone.due_date,
                        'is_past_due': self._is_past_due(tracker_due_date, milestone.due_date),
                        'link_type': link_type
                    })

        return result


reporting_effort_milestone = CRUDReportingEffortMilestone(ReportingEffortMilestone)





