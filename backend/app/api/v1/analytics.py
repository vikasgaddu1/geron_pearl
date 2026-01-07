"""Analytics API endpoints for Director Dashboard."""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.analytics import AnalyticsService
from app.schemas.analytics import (
    ProgrammerVelocityResponse,
    StudyVelocityResponse,
    ProgrammerCapacityResponse,
    TeamCapacityResponse,
    PortfolioHealthResponse,
    StudyHealthStatus,
    TeamUtilizationResponse,
    TeamMemberUtilization,
    DashboardWarnings,
    OrphanedItemWarning,
    OverAllocatedUserWarning,
    MilestoneEstimateResponse,
    CapacityForecastResponse,
    QCMetricsResponse
)
from app.models.user import User as UserModel
from app.core.security import get_current_user

router = APIRouter()


# ==================== PORTFOLIO HEALTH ====================

@router.get("/portfolio-health", response_model=PortfolioHealthResponse)
async def get_portfolio_health(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> PortfolioHealthResponse:
    """
    Get health status for all studies in the portfolio.
    
    Returns progress, risk level, and team capacity for each study.
    """
    service = AnalyticsService(db)
    health_data = await service.get_portfolio_health()
    
    # Build summary counts
    summary = {"on_track": 0, "in_progress": 0, "at_risk": 0, "not_started": 0}
    for study in health_data:
        status = study.get("status", "unknown")
        if status in summary:
            summary[status] += 1
    
    return PortfolioHealthResponse(
        generated_at=datetime.utcnow(),
        studies=[StudyHealthStatus(**s) for s in health_data],
        summary=summary
    )


# ==================== VELOCITY ====================

@router.get("/velocity/study/{study_id}", response_model=StudyVelocityResponse)
async def get_study_velocity(
    study_id: int,
    weeks: int = Query(default=12, ge=1, le=52, description="Number of weeks to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> StudyVelocityResponse:
    """
    Get velocity trend for a study team.
    
    Shows complexity points completed per week over the specified period.
    """
    service = AnalyticsService(db)
    velocity_data = await service.get_study_velocity(study_id, weeks)
    
    return StudyVelocityResponse(**velocity_data)


@router.get("/velocity/user/{user_id}")
async def get_user_velocity(
    user_id: int,
    study_id: Optional[int] = Query(default=None, description="Filter by study"),
    weeks: int = Query(default=8, ge=1, le=52, description="Number of weeks to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get velocity statistics for a programmer.
    
    Returns weekly breakdown and average points per week.
    """
    service = AnalyticsService(db)
    velocity_data = await service.get_programmer_velocity(user_id, study_id, weeks)
    
    if not velocity_data:
        return {
            "user_id": user_id,
            "study_id": study_id,
            "message": "No completion data found",
            "data_points": 0
        }
    
    return velocity_data


# ==================== CAPACITY ====================

@router.get("/capacity/user/{user_id}/study/{study_id}", response_model=ProgrammerCapacityResponse)
async def get_programmer_capacity(
    user_id: int,
    study_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> ProgrammerCapacityResponse:
    """
    Get capacity estimate for a programmer on a study.
    
    Uses actual velocity if available (4+ weeks of data),
    otherwise falls back to factor-based estimation.
    """
    service = AnalyticsService(db)
    capacity_data = await service.get_programmer_capacity(user_id, study_id)
    
    return ProgrammerCapacityResponse(**capacity_data)


@router.get("/capacity/study/{study_id}", response_model=TeamCapacityResponse)
async def get_team_capacity(
    study_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> TeamCapacityResponse:
    """
    Get total team capacity for a study.
    
    Aggregates capacity from all active team members.
    """
    service = AnalyticsService(db)
    capacity_data = await service.get_team_capacity(study_id)
    
    return TeamCapacityResponse(**capacity_data)


# ==================== TEAM UTILIZATION ====================

@router.get("/team-utilization", response_model=TeamUtilizationResponse)
async def get_team_utilization(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> TeamUtilizationResponse:
    """
    Get utilization for all team members across studies.
    
    Shows total allocation and identifies over/under allocation.
    """
    service = AnalyticsService(db)
    utilization_data = await service.get_team_utilization()
    
    over_allocated = sum(1 for m in utilization_data if m["status"] == "over_allocated")
    under_utilized = sum(1 for m in utilization_data if m["status"] == "under_utilized")
    
    return TeamUtilizationResponse(
        generated_at=datetime.utcnow(),
        members=[TeamMemberUtilization(**m) for m in utilization_data],
        over_allocated_count=over_allocated,
        under_utilized_count=under_utilized
    )


# ==================== WARNINGS ====================

@router.get("/warnings", response_model=DashboardWarnings)
async def get_dashboard_warnings(
    study_id: Optional[int] = Query(default=None, description="Filter by study"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> DashboardWarnings:
    """
    Get all warnings for the dashboard.
    
    Includes:
    - Items assigned to inactive team members (orphaned)
    - Users with total allocation > 100% (over-allocated)
    """
    service = AnalyticsService(db)
    
    orphaned = await service.get_orphaned_items(study_id)
    over_allocated = await service.get_over_allocated_users()
    
    return DashboardWarnings(
        orphaned_items=[OrphanedItemWarning(**o) for o in orphaned],
        over_allocated_users=[OverAllocatedUserWarning(**u) for u in over_allocated],
        has_warnings=len(orphaned) > 0 or len(over_allocated) > 0
    )


@router.get("/warnings/orphaned-items", response_model=List[OrphanedItemWarning])
async def get_orphaned_items(
    study_id: Optional[int] = Query(default=None, description="Filter by study"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> List[OrphanedItemWarning]:
    """
    Get items assigned to inactive team members.
    
    These items need to be reassigned to active team members.
    """
    service = AnalyticsService(db)
    orphaned = await service.get_orphaned_items(study_id)
    
    return [OrphanedItemWarning(**o) for o in orphaned]


@router.get("/warnings/over-allocated", response_model=List[OverAllocatedUserWarning])
async def get_over_allocated_users(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> List[OverAllocatedUserWarning]:
    """
    Get users whose total allocation exceeds 100%.
    """
    service = AnalyticsService(db)
    over_allocated = await service.get_over_allocated_users()
    
    return [OverAllocatedUserWarning(**u) for u in over_allocated]


# ==================== ESTIMATION ====================

@router.get("/milestone/{milestone_id}/estimate", response_model=MilestoneEstimateResponse)
async def estimate_milestone_due_date(
    milestone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> MilestoneEstimateResponse:
    """
    Estimate due date for a milestone based on team velocity.
    
    Accounts for:
    - Remaining complexity points
    - Team capacity (velocity or factor-based)
    - Sister study code reuse (if applicable)
    """
    service = AnalyticsService(db)
    estimate = await service.estimate_milestone_due_date(milestone_id)
    
    if "error" in estimate and estimate["error"]:
        return MilestoneEstimateResponse(
            milestone_id=milestone_id,
            milestone_name=estimate.get("milestone_name", "Unknown"),
            remaining_items=0,
            remaining_complexity=0,
            team_points_per_week=0,
            weeks_needed=None,
            start_date=datetime.utcnow().date().isoformat(),
            estimated_due_date=None,
            original_due_date=None,
            error=estimate["error"]
        )
    
    return MilestoneEstimateResponse(**estimate)


# ==================== CAPACITY FORECAST ====================

@router.get("/capacity-forecast", response_model=CapacityForecastResponse)
async def get_capacity_forecast(
    weeks: int = Query(default=8, ge=1, le=26, description="Number of weeks to forecast"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> CapacityForecastResponse:
    """
    Forecast team capacity for upcoming weeks.
    
    Accounts for:
    - Known team member departures
    - Planned team member additions
    """
    service = AnalyticsService(db)
    forecast = await service.get_capacity_forecast(weeks)
    
    return CapacityForecastResponse(**forecast)


# ==================== QC METRICS ====================

@router.get("/qc-metrics", response_model=QCMetricsResponse)
async def get_qc_metrics(
    study_id: Optional[int] = Query(default=None, description="Filter by study"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
) -> QCMetricsResponse:
    """
    Get QC metrics for the dashboard.
    
    Includes first-pass QC rate and item counts.
    """
    service = AnalyticsService(db)
    metrics = await service.get_qc_metrics(study_id, days)
    
    return QCMetricsResponse(**metrics)


# ==================== ESTIMATION ACCURACY ====================

@router.get("/estimation-accuracy")
async def get_estimation_accuracy(
    study_id: Optional[int] = Query(default=None, description="Filter by study"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get estimation accuracy metrics (factor-based vs actual velocity).
    
    Shows how well the system's predictions match reality.
    """
    # This would compare factor-based estimates with actual velocity
    # For now, return placeholder indicating this is planned
    return {
        "study_id": study_id,
        "message": "Estimation accuracy tracking will be available once sufficient completion data is collected",
        "minimum_data_required": "4 weeks of completion data per programmer"
    }

