"""CRUD operations for MilestoneTrackerAssignment."""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.milestone_tracker_assignment import MilestoneTrackerAssignment
from app.models.reporting_effort_milestone import ReportingEffortMilestone
from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
from app.schemas.milestone_tracker_assignment import MilestoneTrackerAssignmentCreate


class CRUDMilestoneTrackerAssignment:
    """CRUD operations for MilestoneTrackerAssignment."""

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: MilestoneTrackerAssignmentCreate
    ) -> MilestoneTrackerAssignment:
        """Create a new milestone-tracker assignment."""
        db_obj = MilestoneTrackerAssignment(
            milestone_id=obj_in.milestone_id,
            tracker_id=obj_in.tracker_id
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
    ) -> Optional[MilestoneTrackerAssignment]:
        """Get an assignment by ID."""
        result = await db.execute(
            select(MilestoneTrackerAssignment).where(MilestoneTrackerAssignment.id == id)
        )
        return result.scalar_one_or_none()

    async def get_assignment(
        self,
        db: AsyncSession,
        *,
        milestone_id: int,
        tracker_id: int
    ) -> Optional[MilestoneTrackerAssignment]:
        """Get a specific assignment by milestone and tracker IDs."""
        result = await db.execute(
            select(MilestoneTrackerAssignment).where(
                and_(
                    MilestoneTrackerAssignment.milestone_id == milestone_id,
                    MilestoneTrackerAssignment.tracker_id == tracker_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def delete(
        self,
        db: AsyncSession,
        *,
        milestone_id: int,
        tracker_id: int
    ) -> bool:
        """Delete an assignment by milestone and tracker IDs."""
        result = await db.execute(
            delete(MilestoneTrackerAssignment).where(
                and_(
                    MilestoneTrackerAssignment.milestone_id == milestone_id,
                    MilestoneTrackerAssignment.tracker_id == tracker_id
                )
            )
        )
        await db.commit()
        return result.rowcount > 0

    async def get_by_milestone(
        self,
        db: AsyncSession,
        *,
        milestone_id: int
    ) -> List[MilestoneTrackerAssignment]:
        """Get all assignments for a milestone."""
        result = await db.execute(
            select(MilestoneTrackerAssignment)
            .where(MilestoneTrackerAssignment.milestone_id == milestone_id)
            .order_by(MilestoneTrackerAssignment.created_at)
        )
        return list(result.scalars().all())

    async def get_by_tracker(
        self,
        db: AsyncSession,
        *,
        tracker_id: int
    ) -> List[MilestoneTrackerAssignment]:
        """Get all assignments for a tracker."""
        result = await db.execute(
            select(MilestoneTrackerAssignment)
            .where(MilestoneTrackerAssignment.tracker_id == tracker_id)
            .order_by(MilestoneTrackerAssignment.created_at)
        )
        return list(result.scalars().all())

    async def get_tracker_ids_by_milestone(
        self,
        db: AsyncSession,
        *,
        milestone_id: int
    ) -> List[int]:
        """Get list of tracker IDs assigned to a milestone."""
        result = await db.execute(
            select(MilestoneTrackerAssignment.tracker_id)
            .where(MilestoneTrackerAssignment.milestone_id == milestone_id)
        )
        return [row[0] for row in result.all()]

    async def get_milestone_ids_by_tracker(
        self,
        db: AsyncSession,
        *,
        tracker_id: int
    ) -> List[int]:
        """Get list of milestone IDs that a tracker is assigned to."""
        result = await db.execute(
            select(MilestoneTrackerAssignment.milestone_id)
            .where(MilestoneTrackerAssignment.tracker_id == tracker_id)
        )
        return [row[0] for row in result.all()]

    async def bulk_assign(
        self,
        db: AsyncSession,
        *,
        milestone_id: int,
        tracker_ids: List[int]
    ) -> Dict[str, Any]:
        """Assign multiple trackers to a milestone."""
        assigned_count = 0
        errors = []

        for tracker_id in tracker_ids:
            try:
                # Check if already assigned
                existing = await self.get_assignment(
                    db, milestone_id=milestone_id, tracker_id=tracker_id
                )
                if existing:
                    continue

                db_obj = MilestoneTrackerAssignment(
                    milestone_id=milestone_id,
                    tracker_id=tracker_id
                )
                db.add(db_obj)
                assigned_count += 1
            except Exception as e:
                errors.append(f"Tracker {tracker_id}: {str(e)}")

        await db.commit()

        return {
            "success": len(errors) == 0,
            "affected_count": assigned_count,
            "errors": errors
        }

    async def bulk_remove(
        self,
        db: AsyncSession,
        *,
        milestone_id: int,
        tracker_ids: List[int]
    ) -> Dict[str, Any]:
        """Remove multiple trackers from a milestone."""
        result = await db.execute(
            delete(MilestoneTrackerAssignment).where(
                and_(
                    MilestoneTrackerAssignment.milestone_id == milestone_id,
                    MilestoneTrackerAssignment.tracker_id.in_(tracker_ids)
                )
            )
        )
        await db.commit()

        return {
            "success": True,
            "affected_count": result.rowcount,
            "errors": []
        }

    async def get_assignments_for_trackers_bulk(
        self,
        db: AsyncSession,
        *,
        tracker_ids: List[int]
    ) -> Dict[int, List[int]]:
        """Get milestone assignments for multiple trackers.

        Returns: Dict mapping tracker_id -> list of milestone_ids
        """
        if not tracker_ids:
            return {}

        result = await db.execute(
            select(MilestoneTrackerAssignment)
            .where(MilestoneTrackerAssignment.tracker_id.in_(tracker_ids))
        )
        assignments = result.scalars().all()

        tracker_milestones: Dict[int, List[int]] = {tid: [] for tid in tracker_ids}
        for assignment in assignments:
            tracker_milestones[assignment.tracker_id].append(assignment.milestone_id)

        return tracker_milestones

    async def update_tracker_milestones(
        self,
        db: AsyncSession,
        *,
        tracker_id: int,
        milestone_ids: List[int]
    ) -> Dict[str, Any]:
        """Update all milestone assignments for a tracker.

        Removes existing assignments and adds new ones for the provided milestone IDs.
        This only affects manual links (junction table), not subtype/tag links.
        """
        # Get current manual assignments
        current_assignments = await self.get_by_tracker(db, tracker_id=tracker_id)
        current_milestone_ids = {a.milestone_id for a in current_assignments}
        new_milestone_ids = set(milestone_ids)

        # Calculate diff
        to_remove = current_milestone_ids - new_milestone_ids
        to_add = new_milestone_ids - current_milestone_ids

        # Remove assignments not in new list
        if to_remove:
            await db.execute(
                delete(MilestoneTrackerAssignment).where(
                    and_(
                        MilestoneTrackerAssignment.tracker_id == tracker_id,
                        MilestoneTrackerAssignment.milestone_id.in_(to_remove)
                    )
                )
            )

        # Add new assignments
        for milestone_id in to_add:
            db_obj = MilestoneTrackerAssignment(
                milestone_id=milestone_id,
                tracker_id=tracker_id
            )
            db.add(db_obj)

        await db.commit()

        return {
            "success": True,
            "added": len(to_add),
            "removed": len(to_remove),
            "total": len(milestone_ids)
        }


milestone_tracker_assignment = CRUDMilestoneTrackerAssignment()
