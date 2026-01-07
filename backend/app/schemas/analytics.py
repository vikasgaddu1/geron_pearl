"""Schemas for Analytics API responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime


# ==================== VELOCITY SCHEMAS ====================

class WeeklyDataPoint(BaseModel):
    """Weekly data for velocity charts."""
    iso_year: int
    iso_week: int
    complexity_points: int
    item_count: int


class ProgrammerVelocityResponse(BaseModel):
    """Programmer velocity statistics."""
    user_id: int
    username: str
    study_id: Optional[int] = None
    study_label: Optional[str] = None
    weeks_analyzed: int
    total_complexity_points: int
    total_items_completed: int
    avg_points_per_week: float
    weekly_data: List[WeeklyDataPoint]
    data_points: int
    confidence: str


class StudyVelocityResponse(BaseModel):
    """Study team velocity statistics."""
    study_id: int
    weeks_analyzed: int
    total_complexity_points: int
    total_items_completed: int
    avg_points_per_week: float
    weekly_data: List[Dict[str, Any]]


# ==================== CAPACITY SCHEMAS ====================

class CapacityFactors(BaseModel):
    """Factors used for factor-based capacity estimation."""
    allocation_percentage: int
    productive_time_factor: int
    experience_level: str
    experience_multiplier: float
    weekly_hours: float


class ProgrammerCapacityResponse(BaseModel):
    """Capacity estimate for a programmer."""
    user_id: int
    study_id: int
    points_per_week: float
    source: str = Field(..., description="velocity or factors")
    confidence: str
    data_points: int
    factors: Optional[CapacityFactors] = None


class TeamMemberCapacity(BaseModel):
    """Capacity for a team member."""
    user_id: int
    username: str
    job_type: str
    points_per_week: float
    source: str
    confidence: str


class TeamCapacityResponse(BaseModel):
    """Total team capacity for a study."""
    study_id: int
    total_points_per_week: float
    member_count: int
    members: List[TeamMemberCapacity]


# ==================== PORTFOLIO HEALTH SCHEMAS ====================

class StudyHealthStatus(BaseModel):
    """Health status for a single study."""
    study_id: int
    study_label: str
    total_items: int
    completed_items: int
    in_progress_items: int
    progress_percentage: float
    total_complexity: int
    completed_complexity: int
    complexity_progress_percentage: float
    status: str = Field(..., description="on_track, in_progress, at_risk, not_started")
    risk: str = Field(..., description="low, medium, high")
    team_size: int
    team_capacity_points_per_week: float


class PortfolioHealthResponse(BaseModel):
    """Portfolio health overview."""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    studies: List[StudyHealthStatus]
    summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by status: on_track, in_progress, at_risk"
    )


# ==================== TEAM UTILIZATION SCHEMAS ====================

class AssignmentDetail(BaseModel):
    """Assignment detail for utilization."""
    study_id: int
    study_label: str
    allocation_percentage: int
    job_type: str


class TeamMemberUtilization(BaseModel):
    """Utilization for a team member."""
    user_id: int
    username: str
    total_allocation_percentage: int
    study_count: int
    status: str = Field(..., description="healthy, over_allocated, under_utilized")
    assignments: List[AssignmentDetail]


class TeamUtilizationResponse(BaseModel):
    """Team utilization overview."""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    members: List[TeamMemberUtilization]
    over_allocated_count: int = 0
    under_utilized_count: int = 0


# ==================== WARNING SCHEMAS ====================

class OrphanedItemWarning(BaseModel):
    """Warning about items assigned to inactive members."""
    user_id: int
    username: str
    study_id: int
    study_label: str
    departure_reason: Optional[str]
    departure_date: Optional[date]
    orphaned_item_count: int


class OverAllocatedUserWarning(BaseModel):
    """Warning about over-allocated users."""
    user_id: int
    username: str
    total_allocation: int


class DashboardWarnings(BaseModel):
    """All warnings for the dashboard."""
    orphaned_items: List[OrphanedItemWarning]
    over_allocated_users: List[OverAllocatedUserWarning]
    has_warnings: bool


# ==================== ESTIMATION SCHEMAS ====================

class SisterStudyAdjustment(BaseModel):
    """Sister study impact on estimates."""
    has_sister_study: bool
    sister_study_id: Optional[int]
    code_reuse_percentage: int
    original_estimate: float
    adjusted_estimate: float
    reduction_percentage: float


class MilestoneEstimateResponse(BaseModel):
    """Milestone due date estimation."""
    milestone_id: int
    milestone_name: str
    remaining_items: int
    remaining_complexity: int
    team_points_per_week: float
    weeks_needed: Optional[float]
    start_date: str
    estimated_due_date: Optional[str]
    original_due_date: Optional[str]
    sister_study_adjustment: Optional[SisterStudyAdjustment]
    status: Optional[str] = None
    error: Optional[str] = None


# ==================== CAPACITY FORECAST SCHEMAS ====================

class ForecastWeek(BaseModel):
    """Forecast data for a single week."""
    week_start: str
    week_number: int
    total_allocation_percentage: int
    fte: float


class CapacityForecastResponse(BaseModel):
    """Capacity forecast for upcoming weeks."""
    forecast_weeks: int
    generated_at: str
    weeks: List[ForecastWeek]


# ==================== QC METRICS SCHEMAS ====================

class QCMetricsResponse(BaseModel):
    """QC metrics for dashboard."""
    period_days: int
    study_id: Optional[int]
    total_items_processed: int
    qc_completed: int
    qc_failed: int
    first_pass_rate_percentage: float


# ==================== BURNDOWN SCHEMAS ====================

class BurndownDataPoint(BaseModel):
    """Burndown chart data point."""
    date: str
    remaining_items: int
    remaining_complexity: int
    completed_items: int
    completed_complexity: int


class BurndownResponse(BaseModel):
    """Burndown data for a study."""
    study_id: int
    study_label: str
    total_items: int
    total_complexity: int
    data_points: List[BurndownDataPoint]
    projected_completion_date: Optional[str]

