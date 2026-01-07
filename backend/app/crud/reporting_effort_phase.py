"""CRUD operations for ReportingEffortPhase."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import BaseCRUD
from app.models.reporting_effort_phase import ReportingEffortPhase
from app.models.reporting_effort_milestone import ReportingEffortMilestone
from app.schemas.reporting_effort_phase import (
    ReportingEffortPhaseCreate,
    ReportingEffortPhaseUpdate
)


class CRUDReportingEffortPhase(BaseCRUD[ReportingEffortPhase, ReportingEffortPhaseCreate, ReportingEffortPhaseUpdate]):
    """CRUD operations for ReportingEffortPhase."""
    
    async def get_by_reporting_effort(
        self, 
        db: AsyncSession, 
        *, 
        reporting_effort_id: int
    ) -> List[ReportingEffortPhase]:
        """Get all phases for a reporting effort, ordered by display_order."""
        result = await db.execute(
            select(ReportingEffortPhase)
            .where(ReportingEffortPhase.reporting_effort_id == reporting_effort_id)
            .order_by(ReportingEffortPhase.display_order)
        )
        return list(result.scalars().all())
    
    async def get_with_milestones(
        self, 
        db: AsyncSession, 
        *, 
        phase_id: int
    ) -> Optional[ReportingEffortPhase]:
        """Get a phase with its milestones."""
        result = await db.execute(
            select(ReportingEffortPhase)
            .options(selectinload(ReportingEffortPhase.milestones))
            .where(ReportingEffortPhase.id == phase_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_with_milestones(
        self, 
        db: AsyncSession, 
        *, 
        reporting_effort_id: int
    ) -> List[ReportingEffortPhase]:
        """Get all phases for a reporting effort with their milestones."""
        result = await db.execute(
            select(ReportingEffortPhase)
            .options(selectinload(ReportingEffortPhase.milestones))
            .where(ReportingEffortPhase.reporting_effort_id == reporting_effort_id)
            .order_by(ReportingEffortPhase.display_order)
        )
        return list(result.scalars().all())
    
    async def get_next_display_order(
        self, 
        db: AsyncSession, 
        *, 
        reporting_effort_id: int
    ) -> int:
        """Get the next display order for a new phase."""
        result = await db.execute(
            select(ReportingEffortPhase.display_order)
            .where(ReportingEffortPhase.reporting_effort_id == reporting_effort_id)
            .order_by(ReportingEffortPhase.display_order.desc())
            .limit(1)
        )
        max_order = result.scalar_one_or_none()
        return (max_order or 0) + 1
    
    async def reorder_phases(
        self, 
        db: AsyncSession, 
        *, 
        reporting_effort_id: int,
        phase_ids: List[int]
    ) -> List[ReportingEffortPhase]:
        """Reorder phases by updating their display_order based on the given ID list."""
        phases = await self.get_by_reporting_effort(db, reporting_effort_id=reporting_effort_id)
        phase_map = {p.id: p for p in phases}
        
        for order, phase_id in enumerate(phase_ids):
            if phase_id in phase_map:
                phase_map[phase_id].display_order = order
        
        await db.commit()
        return await self.get_by_reporting_effort(db, reporting_effort_id=reporting_effort_id)


reporting_effort_phase = CRUDReportingEffortPhase(ReportingEffortPhase)






