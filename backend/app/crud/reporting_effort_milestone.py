"""CRUD operations for ReportingEffortMilestone."""

from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.crud.base import BaseCRUD
from app.models.reporting_effort_milestone import ReportingEffortMilestone
from app.models.reporting_effort_phase import ReportingEffortPhase
from app.models.reporting_effort import ReportingEffort
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


reporting_effort_milestone = CRUDReportingEffortMilestone(ReportingEffortMilestone)

