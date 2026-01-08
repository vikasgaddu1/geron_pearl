"""CRUD operations for StudyTeamAssignment."""

from typing import List, Optional
from datetime import date
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import BaseCRUD
from app.models.study_team_assignment import StudyTeamAssignment, JobType, DepartureReason
from app.models.user import User
from app.models.study import Study
from app.schemas.study_team_assignment import (
    StudyTeamAssignmentCreate, 
    StudyTeamAssignmentUpdate,
    ChangeAllocationRequest,
    EndAssignmentRequest
)


class StudyTeamAssignmentCRUD(BaseCRUD[StudyTeamAssignment, StudyTeamAssignmentCreate, StudyTeamAssignmentUpdate]):
    """CRUD operations for StudyTeamAssignment with allocation history support."""

    async def get_active_assignment(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        study_id: int
    ) -> Optional[StudyTeamAssignment]:
        """Get the current active assignment for a user on a study."""
        result = await db.execute(
            select(StudyTeamAssignment).where(
                and_(
                    StudyTeamAssignment.user_id == user_id,
                    StudyTeamAssignment.study_id == study_id,
                    StudyTeamAssignment.is_active == True,
                    StudyTeamAssignment.effective_end_date.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_study(
        self, 
        db: AsyncSession, 
        *, 
        study_id: int
    ) -> List[StudyTeamAssignment]:
        """Get all active team assignments for a study."""
        result = await db.execute(
            select(StudyTeamAssignment)
            .where(
                and_(
                    StudyTeamAssignment.study_id == study_id,
                    StudyTeamAssignment.is_active == True,
                    StudyTeamAssignment.effective_end_date.is_(None)
                )
            )
            .options(selectinload(StudyTeamAssignment.user))
            .order_by(StudyTeamAssignment.job_type, StudyTeamAssignment.created_at)
        )
        return list(result.scalars().all())

    async def get_active_by_user(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int
    ) -> List[StudyTeamAssignment]:
        """Get all active study assignments for a user."""
        result = await db.execute(
            select(StudyTeamAssignment)
            .where(
                and_(
                    StudyTeamAssignment.user_id == user_id,
                    StudyTeamAssignment.is_active == True,
                    StudyTeamAssignment.effective_end_date.is_(None)
                )
            )
            .options(selectinload(StudyTeamAssignment.study))
            .order_by(StudyTeamAssignment.effective_start_date.desc())
        )
        return list(result.scalars().all())

    async def get_allocation_history(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        study_id: int
    ) -> List[StudyTeamAssignment]:
        """Get all assignment records for a user on a study (full history)."""
        result = await db.execute(
            select(StudyTeamAssignment)
            .where(
                and_(
                    StudyTeamAssignment.user_id == user_id,
                    StudyTeamAssignment.study_id == study_id
                )
            )
            .order_by(StudyTeamAssignment.effective_start_date.desc())
        )
        return list(result.scalars().all())

    async def get_user_total_allocation(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int
    ) -> int:
        """Get total allocation percentage across all active studies for a user."""
        result = await db.execute(
            select(func.sum(StudyTeamAssignment.allocation_percentage))
            .where(
                and_(
                    StudyTeamAssignment.user_id == user_id,
                    StudyTeamAssignment.is_active == True,
                    StudyTeamAssignment.effective_end_date.is_(None)
                )
            )
        )
        total = result.scalar()
        return total or 0

    async def add_team_member(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int,
        study_id: int,
        job_type: str,
        allocation_percentage: int = 100,
        productive_time_factor: int = 75,
        experience_level: str = "MID",
        effective_start_date: date,
        notes: Optional[str] = None
    ) -> StudyTeamAssignment:
        """
        Add a new team member to a study.
        
        Raises ValueError if user already has an active assignment on this study.
        """
        # Check for existing active assignment
        existing = await self.get_active_assignment(db, user_id=user_id, study_id=study_id)
        if existing:
            raise ValueError(
                f"User {user_id} already has an active assignment on study {study_id}. "
                "Use change_allocation() to modify or end_assignment() to close first."
            )
        
        obj_in = StudyTeamAssignmentCreate(
            user_id=user_id,
            study_id=study_id,
            job_type=job_type,
            allocation_percentage=allocation_percentage,
            productive_time_factor=productive_time_factor,
            experience_level=experience_level,
            effective_start_date=effective_start_date,
            notes=notes
        )
        return await self.create(db, obj_in=obj_in)

    async def change_allocation(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int,
        study_id: int,
        request: ChangeAllocationRequest
    ) -> StudyTeamAssignment:
        """
        Change a team member's allocation.
        
        This closes the current assignment and creates a new one to preserve history.
        """
        current = await self.get_active_assignment(db, user_id=user_id, study_id=study_id)
        if not current:
            raise ValueError(f"No active assignment found for user {user_id} on study {study_id}")
        
        # Close the current assignment
        current.effective_end_date = request.effective_date
        current.is_active = False
        current.departure_reason = DepartureReason.ALLOCATION_CHANGED.value
        
        # Create new assignment with updated values
        new_assignment = StudyTeamAssignment(
            user_id=user_id,
            study_id=study_id,
            job_type=request.new_job_type or current.job_type,
            allocation_percentage=request.new_allocation_percentage,
            productive_time_factor=request.new_productive_time_factor or current.productive_time_factor,
            experience_level=request.new_experience_level or current.experience_level,
            effective_start_date=request.effective_date,
            is_active=True,
            notes=request.notes
        )
        
        db.add(new_assignment)
        await db.commit()
        await db.refresh(new_assignment)
        
        return new_assignment

    async def end_assignment(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int,
        study_id: int,
        request: EndAssignmentRequest
    ) -> StudyTeamAssignment:
        """
        End a team member's assignment on a study.
        
        The assignment record is preserved with departure info.
        Items assigned to this user will remain assigned but should be flagged for reassignment.
        """
        current = await self.get_active_assignment(db, user_id=user_id, study_id=study_id)
        if not current:
            raise ValueError(f"No active assignment found for user {user_id} on study {study_id}")
        
        current.effective_end_date = request.effective_date
        current.is_active = False
        current.departure_reason = request.departure_reason
        if request.notes:
            current.notes = (current.notes or "") + f"\n[End: {request.notes}]"
        
        await db.commit()
        await db.refresh(current)
        
        return current

    async def get_inactive_members_with_items(
        self, 
        db: AsyncSession, 
        *, 
        study_id: Optional[int] = None
    ) -> List[dict]:
        """
        Find inactive team members who still have tracker items assigned.
        
        Returns list of dicts with user info and count of orphaned items.
        """
        from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
        from app.models.reporting_effort_item import ReportingEffortItem
        from app.models.reporting_effort import ReportingEffort
        
        # Build base query for inactive assignments
        query = (
            select(
                StudyTeamAssignment.user_id,
                StudyTeamAssignment.study_id,
                StudyTeamAssignment.departure_reason,
                StudyTeamAssignment.effective_end_date,
                User.username,
                Study.study_label,
                func.count(ReportingEffortItemTracker.id).label('orphaned_count')
            )
            .join(User, StudyTeamAssignment.user_id == User.id)
            .join(Study, StudyTeamAssignment.study_id == Study.id)
            .outerjoin(
                ReportingEffortItemTracker,
                and_(
                    ReportingEffortItemTracker.production_programmer_id == StudyTeamAssignment.user_id,
                    ReportingEffortItemTracker.production_status != 'completed'
                )
            )
            .outerjoin(
                ReportingEffortItem,
                ReportingEffortItemTracker.reporting_effort_item_id == ReportingEffortItem.id
            )
            .outerjoin(
                ReportingEffort,
                ReportingEffortItem.reporting_effort_id == ReportingEffort.id
            )
            .where(
                and_(
                    StudyTeamAssignment.is_active == False,
                    StudyTeamAssignment.effective_end_date.isnot(None)
                )
            )
            .group_by(
                StudyTeamAssignment.user_id,
                StudyTeamAssignment.study_id,
                StudyTeamAssignment.departure_reason,
                StudyTeamAssignment.effective_end_date,
                User.username,
                Study.study_label
            )
            .having(func.count(ReportingEffortItemTracker.id) > 0)
        )
        
        if study_id:
            query = query.where(StudyTeamAssignment.study_id == study_id)
        
        result = await db.execute(query)
        rows = result.all()
        
        return [
            {
                "user_id": row.user_id,
                "username": row.username,
                "study_id": row.study_id,
                "study_label": row.study_label,
                "departure_reason": row.departure_reason,
                "departure_date": row.effective_end_date,
                "orphaned_item_count": row.orphaned_count
            }
            for row in rows
        ]

    async def get_study_team_capacity(
        self, 
        db: AsyncSession, 
        *, 
        study_id: int
    ) -> dict:
        """
        Calculate total team capacity for a study.
        
        Returns dict with:
        - total_allocation: Sum of all allocation percentages
        - total_weekly_hours: Sum of effective weekly productive hours
        - member_count: Number of active team members
        """
        assignments = await self.get_active_by_study(db, study_id=study_id)
        
        total_allocation = sum(a.allocation_percentage for a in assignments)
        total_weekly_hours = sum(a.effective_weekly_hours for a in assignments)
        
        return {
            "total_allocation": total_allocation,
            "total_weekly_hours": total_weekly_hours,
            "member_count": len(assignments)
        }

    async def get_programmers_by_job_type(
        self, 
        db: AsyncSession, 
        *, 
        study_id: int,
        job_type: str
    ) -> List[StudyTeamAssignment]:
        """Get active team members with a specific job type."""
        result = await db.execute(
            select(StudyTeamAssignment)
            .where(
                and_(
                    StudyTeamAssignment.study_id == study_id,
                    StudyTeamAssignment.job_type == job_type,
                    StudyTeamAssignment.is_active == True,
                    StudyTeamAssignment.effective_end_date.is_(None)
                )
            )
            .options(selectinload(StudyTeamAssignment.user))
        )
        return list(result.scalars().all())

    async def get_over_allocated_users(
        self, 
        db: AsyncSession
    ) -> List[dict]:
        """Find users whose total allocation across studies exceeds 100%."""
        result = await db.execute(
            select(
                StudyTeamAssignment.user_id,
                User.username,
                func.sum(StudyTeamAssignment.allocation_percentage).label('total_allocation')
            )
            .join(User, StudyTeamAssignment.user_id == User.id)
            .where(
                and_(
                    StudyTeamAssignment.is_active == True,
                    StudyTeamAssignment.effective_end_date.is_(None)
                )
            )
            .group_by(StudyTeamAssignment.user_id, User.username)
            .having(func.sum(StudyTeamAssignment.allocation_percentage) > 100)
        )
        rows = result.all()
        
        return [
            {
                "user_id": row.user_id,
                "username": row.username,
                "total_allocation": row.total_allocation
            }
            for row in rows
        ]


# Singleton instance
study_team_assignment = StudyTeamAssignmentCRUD(StudyTeamAssignment)

