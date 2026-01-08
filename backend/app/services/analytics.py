"""Analytics Service for throughput-based estimation and director dashboard.

This service aggregates data from:
- StudyTeamAssignment (team capacity)
- ItemCompletionRecord (velocity calculations)
- StudySisterRelation (code reuse impact)
- ReportingEffortItemTracker (current work status)

Provides:
- Programmer velocity (complexity points per week)
- Team capacity and utilization
- Milestone due date estimation
- Portfolio health overview
- Capacity forecasting
- QC metrics
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy import select, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study import Study
from app.models.user import User
from app.models.study_team_assignment import StudyTeamAssignment, EXPERIENCE_MULTIPLIERS, ExperienceLevel
from app.models.item_completion_record import ItemCompletionRecord
from app.models.study_sister_relation import StudySisterRelation
from app.models.reporting_effort_item_tracker import ReportingEffortItemTracker
from app.models.reporting_effort_item import ReportingEffortItem
from app.models.reporting_effort import ReportingEffort
from app.crud.item_completion_record import item_completion_record as completion_crud
from app.crud.study_team_assignment import study_team_assignment as team_crud
from app.crud.study_sister_relation import study_sister_relation as sister_crud


class AnalyticsService:
    """
    Central analytics service for the Director Dashboard.
    
    Uses throughput-based estimation:
    - For members with history: Uses actual velocity from completions
    - For new members: Uses factor-based estimates (allocation × productive_time × experience)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== VELOCITY CALCULATIONS ====================
    
    async def get_programmer_velocity(
        self,
        user_id: int,
        study_id: Optional[int] = None,
        weeks: int = 8
    ) -> Optional[Dict[str, Any]]:
        """
        Get velocity statistics for a programmer.
        
        Returns None if no completion data exists.
        """
        return await completion_crud.get_programmer_velocity(
            self.db,
            user_id=user_id,
            study_id=study_id,
            weeks=weeks
        )
    
    async def get_study_velocity(
        self,
        study_id: int,
        weeks: int = 12
    ) -> Dict[str, Any]:
        """
        Get team velocity for a study.
        """
        return await completion_crud.get_study_velocity(
            self.db,
            study_id=study_id,
            weeks=weeks
        )
    
    # ==================== CAPACITY CALCULATIONS ====================
    
    async def get_programmer_capacity(
        self,
        user_id: int,
        study_id: int
    ) -> Dict[str, Any]:
        """
        Get capacity estimate for a programmer on a study.
        
        Uses velocity if available (4+ weeks of data), otherwise factors.
        """
        # Try to get actual velocity
        velocity = await self.get_programmer_velocity(user_id, study_id, weeks=8)
        
        if velocity and velocity.data_points >= 4:
            # Use actual velocity
            return {
                "user_id": user_id,
                "study_id": study_id,
                "points_per_week": velocity.avg_points_per_week,
                "source": "velocity",
                "confidence": velocity.confidence,
                "data_points": velocity.data_points
            }
        
        # Fall back to factor-based estimate
        assignment = await team_crud.get_active_assignment(
            self.db,
            user_id=user_id,
            study_id=study_id
        )
        
        if not assignment:
            return {
                "user_id": user_id,
                "study_id": study_id,
                "points_per_week": 0,
                "source": "no_assignment",
                "confidence": "none",
                "data_points": 0
            }
        
        # Calculate from factors
        # Base: 40 hours/week × allocation% × productive_time%
        # Then divide by estimated hours per complexity point (adjusted for experience)
        weekly_hours = assignment.effective_weekly_hours
        experience_mult = assignment.experience_multiplier
        base_hours_per_point = 4.0  # Default: complexity × 4 hours
        
        points_per_week = weekly_hours / (base_hours_per_point * experience_mult)
        
        return {
            "user_id": user_id,
            "study_id": study_id,
            "points_per_week": round(points_per_week, 2),
            "source": "factors",
            "confidence": "low",
            "data_points": 0,
            "factors": {
                "allocation_percentage": assignment.allocation_percentage,
                "productive_time_factor": assignment.productive_time_factor,
                "experience_level": assignment.experience_level,
                "experience_multiplier": experience_mult,
                "weekly_hours": weekly_hours
            }
        }
    
    async def get_team_capacity(
        self,
        study_id: int
    ) -> Dict[str, Any]:
        """
        Get total team capacity for a study.
        """
        assignments = await team_crud.get_active_by_study(self.db, study_id=study_id)
        
        member_capacities = []
        total_points_per_week = 0
        
        for assignment in assignments:
            capacity = await self.get_programmer_capacity(
                assignment.user_id,
                study_id
            )
            member_capacities.append({
                **capacity,
                "username": assignment.user.username,
                "job_type": assignment.job_type
            })
            total_points_per_week += capacity["points_per_week"]
        
        return {
            "study_id": study_id,
            "total_points_per_week": round(total_points_per_week, 2),
            "member_count": len(assignments),
            "members": member_capacities
        }
    
    # ==================== ESTIMATION ====================
    
    async def estimate_milestone_due_date(
        self,
        milestone_id: int
    ) -> Dict[str, Any]:
        """
        Estimate due date for a milestone based on team velocity and remaining work.
        """
        from app.models.reporting_effort_milestone import ReportingEffortMilestone
        from app.models.reporting_effort_phase import ReportingEffortPhase
        from app.models.milestone_tracker_assignment import MilestoneTrackerAssignment
        
        # Get milestone
        milestone_result = await self.db.execute(
            select(ReportingEffortMilestone)
            .where(ReportingEffortMilestone.id == milestone_id)
        )
        milestone = milestone_result.scalar_one_or_none()
        if not milestone:
            return {"error": "Milestone not found"}
        
        # Get phase to find reporting effort
        phase_result = await self.db.execute(
            select(ReportingEffortPhase)
            .where(ReportingEffortPhase.id == milestone.phase_id)
        )
        phase = phase_result.scalar_one_or_none()
        if not phase:
            return {"error": "Phase not found"}
        
        # Get reporting effort for study_id
        effort_result = await self.db.execute(
            select(ReportingEffort)
            .where(ReportingEffort.id == phase.reporting_effort_id)
        )
        effort = effort_result.scalar_one_or_none()
        study_id = effort.study_id if effort else None
        
        # Get items linked to this milestone (via subtype, tag, or manual assignment)
        tracker_ids = []
        
        # Get manual assignments
        manual_result = await self.db.execute(
            select(MilestoneTrackerAssignment.tracker_id)
            .where(MilestoneTrackerAssignment.milestone_id == milestone_id)
        )
        tracker_ids.extend([r.tracker_id for r in manual_result.all()])
        
        # Get by subtype if specified
        if milestone.linked_subtype:
            subtype_result = await self.db.execute(
                select(ReportingEffortItemTracker.id)
                .join(ReportingEffortItem)
                .join(ReportingEffort)
                .where(
                    and_(
                        ReportingEffort.id == phase.reporting_effort_id,
                        ReportingEffortItem.item_subtype == milestone.linked_subtype
                    )
                )
            )
            tracker_ids.extend([r.id for r in subtype_result.all()])
        
        # Remove duplicates
        tracker_ids = list(set(tracker_ids))
        
        if not tracker_ids:
            return {
                "milestone_id": milestone_id,
                "milestone_name": milestone.name,
                "error": "No items linked to milestone"
            }
        
        # Get remaining work (not completed items)
        remaining_result = await self.db.execute(
            select(
                func.count(ReportingEffortItemTracker.id).label('count'),
                func.sum(ReportingEffortItemTracker.complexity).label('complexity_sum')
            )
            .where(
                and_(
                    ReportingEffortItemTracker.id.in_(tracker_ids),
                    ReportingEffortItemTracker.production_status != 'completed'
                )
            )
        )
        remaining = remaining_result.one()
        
        remaining_items = remaining.count or 0
        remaining_complexity = remaining.complexity_sum or 0
        
        if remaining_complexity == 0:
            return {
                "milestone_id": milestone_id,
                "milestone_name": milestone.name,
                "status": "completed",
                "remaining_items": 0,
                "remaining_complexity": 0
            }
        
        # Get team velocity
        if study_id:
            team_capacity = await self.get_team_capacity(study_id)
            points_per_week = team_capacity["total_points_per_week"]
        else:
            points_per_week = 10  # Fallback default
        
        # Calculate weeks needed
        if points_per_week > 0:
            weeks_needed = remaining_complexity / points_per_week
        else:
            weeks_needed = float('inf')
        
        # Calculate estimated due date
        start_date = milestone.start_date or date.today()
        if weeks_needed != float('inf'):
            estimated_due = start_date + timedelta(weeks=weeks_needed)
        else:
            estimated_due = None
        
        # Check sister study impact
        adjustment = None
        if study_id:
            adjustment = await sister_crud.calculate_adjusted_estimate(
                self.db,
                study_id=study_id,
                base_estimate=remaining_complexity
            )
            if adjustment["has_sister_study"]:
                adjusted_complexity = adjustment["adjusted_estimate"]
                adjusted_weeks = adjusted_complexity / points_per_week if points_per_week > 0 else float('inf')
                if adjusted_weeks != float('inf'):
                    estimated_due = start_date + timedelta(weeks=adjusted_weeks)
        
        return {
            "milestone_id": milestone_id,
            "milestone_name": milestone.name,
            "remaining_items": remaining_items,
            "remaining_complexity": remaining_complexity,
            "team_points_per_week": points_per_week,
            "weeks_needed": round(weeks_needed, 1) if weeks_needed != float('inf') else None,
            "start_date": start_date.isoformat(),
            "estimated_due_date": estimated_due.isoformat() if estimated_due else None,
            "original_due_date": milestone.due_date.isoformat() if milestone.due_date else None,
            "sister_study_adjustment": adjustment
        }
    
    # ==================== PORTFOLIO HEALTH ====================
    
    async def get_portfolio_health(self) -> List[Dict[str, Any]]:
        """
        Get health status for all active studies.
        """
        # Get all studies
        studies_result = await self.db.execute(select(Study))
        studies = studies_result.scalars().all()
        
        health_data = []
        
        for study in studies:
            # Get tracker statistics for this study
            stats_result = await self.db.execute(
                select(
                    func.count(ReportingEffortItemTracker.id).label('total'),
                    func.sum(case(
                        (ReportingEffortItemTracker.production_status == 'completed', 1),
                        else_=0
                    )).label('completed'),
                    func.sum(case(
                        (ReportingEffortItemTracker.production_status == 'in_progress', 1),
                        else_=0
                    )).label('in_progress'),
                    func.sum(ReportingEffortItemTracker.complexity).label('total_complexity'),
                    func.sum(case(
                        (ReportingEffortItemTracker.production_status == 'completed', 
                         ReportingEffortItemTracker.complexity),
                        else_=0
                    )).label('completed_complexity')
                )
                .join(ReportingEffortItem)
                .join(ReportingEffort)
                .where(ReportingEffort.study_id == study.id)
            )
            stats = stats_result.one()
            
            total = stats.total or 0
            completed = stats.completed or 0
            in_progress = stats.in_progress or 0
            total_complexity = stats.total_complexity or 0
            completed_complexity = stats.completed_complexity or 0
            
            progress_pct = (completed / total * 100) if total > 0 else 0
            complexity_progress_pct = (completed_complexity / total_complexity * 100) if total_complexity > 0 else 0
            
            # Determine status
            if progress_pct >= 95:
                status = "on_track"
                risk = "low"
            elif progress_pct >= 75:
                status = "on_track"
                risk = "low"
            elif in_progress > 0:
                status = "in_progress"
                risk = "medium"
            elif total == 0:
                status = "not_started"
                risk = "low"
            else:
                status = "at_risk"
                risk = "high"
            
            # Get team info
            team_capacity = await self.get_team_capacity(study.id)
            
            health_data.append({
                "study_id": study.id,
                "study_label": study.study_label,
                "total_items": total,
                "completed_items": completed,
                "in_progress_items": in_progress,
                "progress_percentage": round(progress_pct, 1),
                "total_complexity": total_complexity,
                "completed_complexity": completed_complexity,
                "complexity_progress_percentage": round(complexity_progress_pct, 1),
                "status": status,
                "risk": risk,
                "team_size": team_capacity["member_count"],
                "team_capacity_points_per_week": team_capacity["total_points_per_week"]
            })
        
        return health_data
    
    # ==================== TEAM UTILIZATION ====================
    
    async def get_team_utilization(self) -> List[Dict[str, Any]]:
        """
        Get utilization for all team members across studies.
        """
        # Get all active assignments grouped by user
        result = await self.db.execute(
            select(
                StudyTeamAssignment.user_id,
                User.username,
                func.sum(StudyTeamAssignment.allocation_percentage).label('total_allocation'),
                func.count(StudyTeamAssignment.study_id).label('study_count')
            )
            .join(User, StudyTeamAssignment.user_id == User.id)
            .where(
                and_(
                    StudyTeamAssignment.is_active == True,
                    StudyTeamAssignment.effective_end_date.is_(None)
                )
            )
            .group_by(StudyTeamAssignment.user_id, User.username)
        )
        rows = result.all()
        
        utilization_data = []
        
        for row in rows:
            # Get detailed assignments
            assignments = await team_crud.get_active_by_user(self.db, user_id=row.user_id)
            
            assignment_details = [
                {
                    "study_id": a.study_id,
                    "study_label": a.study.study_label,
                    "allocation_percentage": a.allocation_percentage,
                    "job_type": a.job_type
                }
                for a in assignments
            ]
            
            status = "healthy"
            if row.total_allocation > 100:
                status = "over_allocated"
            elif row.total_allocation < 50:
                status = "under_utilized"
            
            utilization_data.append({
                "user_id": row.user_id,
                "username": row.username,
                "total_allocation_percentage": row.total_allocation,
                "study_count": row.study_count,
                "status": status,
                "assignments": assignment_details
            })
        
        return utilization_data
    
    # ==================== WARNINGS ====================
    
    async def get_orphaned_items(
        self,
        study_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get items assigned to inactive team members.
        """
        return await team_crud.get_inactive_members_with_items(
            self.db,
            study_id=study_id
        )
    
    async def get_over_allocated_users(self) -> List[Dict[str, Any]]:
        """
        Get users with total allocation > 100%.
        """
        return await team_crud.get_over_allocated_users(self.db)
    
    # ==================== QC METRICS ====================
    
    async def get_qc_metrics(
        self,
        study_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get QC metrics for dashboard.
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build base query
        query = (
            select(
                func.count(ReportingEffortItemTracker.id).label('total'),
                func.sum(case(
                    (ReportingEffortItemTracker.qc_status == 'completed', 1),
                    else_=0
                )).label('qc_completed'),
                func.sum(case(
                    (ReportingEffortItemTracker.qc_status == 'failed', 1),
                    else_=0
                )).label('qc_failed')
            )
            .join(ReportingEffortItem)
            .join(ReportingEffort)
            .where(ReportingEffortItemTracker.updated_at >= start_date)
        )
        
        if study_id:
            query = query.where(ReportingEffort.study_id == study_id)
        
        result = await self.db.execute(query)
        stats = result.one()
        
        total = stats.total or 0
        qc_completed = stats.qc_completed or 0
        qc_failed = stats.qc_failed or 0
        
        first_pass_rate = (qc_completed / (qc_completed + qc_failed) * 100) if (qc_completed + qc_failed) > 0 else 0
        
        return {
            "period_days": days,
            "study_id": study_id,
            "total_items_processed": total,
            "qc_completed": qc_completed,
            "qc_failed": qc_failed,
            "first_pass_rate_percentage": round(first_pass_rate, 1)
        }
    
    # ==================== CAPACITY FORECAST ====================
    
    async def get_capacity_forecast(
        self,
        weeks_ahead: int = 8
    ) -> Dict[str, Any]:
        """
        Forecast capacity vs demand for upcoming weeks.
        
        Accounts for:
        - Known team member departures (effective_end_date set)
        - Known team member additions (effective_start_date in future)
        """
        forecast_weeks = []
        today = date.today()
        
        for week_offset in range(weeks_ahead):
            week_start = today + timedelta(weeks=week_offset)
            
            # Get assignments active during this week
            result = await self.db.execute(
                select(func.sum(StudyTeamAssignment.allocation_percentage))
                .where(
                    and_(
                        StudyTeamAssignment.effective_start_date <= week_start,
                        or_(
                            StudyTeamAssignment.effective_end_date.is_(None),
                            StudyTeamAssignment.effective_end_date > week_start
                        )
                    )
                )
            )
            total_allocation = result.scalar() or 0
            
            # Calculate FTE (100% = 1 FTE)
            fte = total_allocation / 100
            
            forecast_weeks.append({
                "week_start": week_start.isoformat(),
                "week_number": week_offset + 1,
                "total_allocation_percentage": total_allocation,
                "fte": round(fte, 2)
            })
        
        return {
            "forecast_weeks": weeks_ahead,
            "generated_at": datetime.utcnow().isoformat(),
            "weeks": forecast_weeks
        }


# Import for backward compatibility with or_ 
from sqlalchemy import or_

