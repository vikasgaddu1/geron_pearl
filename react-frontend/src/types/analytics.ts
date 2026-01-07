/**
 * Analytics types for Director Dashboard
 */

// Weekly velocity data point
export interface WeeklyDataPoint {
  iso_year: number
  iso_week: number
  complexity_points: number
  item_count: number
}

// Portfolio health for a single study
export interface StudyHealthStatus {
  study_id: number
  study_label: string
  total_items: number
  completed_items: number
  in_progress_items: number
  progress_percentage: number
  total_complexity: number
  completed_complexity: number
  complexity_progress_percentage: number
  status: 'on_track' | 'in_progress' | 'at_risk' | 'not_started'
  risk: 'low' | 'medium' | 'high'
  team_size: number
  team_capacity_points_per_week: number
}

export interface PortfolioHealthResponse {
  generated_at: string
  studies: StudyHealthStatus[]
  summary: {
    on_track: number
    in_progress: number
    at_risk: number
    not_started: number
  }
}

// Study velocity
export interface StudyVelocityResponse {
  study_id: number
  weeks_analyzed: number
  total_complexity_points: number
  total_items_completed: number
  avg_points_per_week: number
  weekly_data: WeeklyDataPoint[]
}

// Team utilization
export interface AssignmentDetail {
  study_id: number
  study_label: string
  allocation_percentage: number
  job_type: string
}

export interface TeamMemberUtilization {
  user_id: number
  username: string
  total_allocation_percentage: number
  study_count: number
  status: 'healthy' | 'over_allocated' | 'under_utilized'
  assignments: AssignmentDetail[]
}

export interface TeamUtilizationResponse {
  generated_at: string
  members: TeamMemberUtilization[]
  over_allocated_count: number
  under_utilized_count: number
}

// Warnings
export interface OrphanedItemWarning {
  user_id: number
  username: string
  study_id: number
  study_label: string
  departure_reason: string | null
  departure_date: string | null
  orphaned_item_count: number
}

export interface OverAllocatedUserWarning {
  user_id: number
  username: string
  total_allocation: number
}

export interface DashboardWarnings {
  orphaned_items: OrphanedItemWarning[]
  over_allocated_users: OverAllocatedUserWarning[]
  has_warnings: boolean
}

// Capacity
export interface TeamMemberCapacity {
  user_id: number
  username: string
  job_type: string
  points_per_week: number
  source: 'velocity' | 'factors'
  confidence: 'high' | 'medium' | 'low' | 'none'
}

export interface TeamCapacityResponse {
  study_id: number
  total_points_per_week: number
  member_count: number
  members: TeamMemberCapacity[]
}

// Capacity forecast
export interface ForecastWeek {
  week_start: string
  week_number: number
  total_allocation_percentage: number
  fte: number
}

export interface CapacityForecastResponse {
  forecast_weeks: number
  generated_at: string
  weeks: ForecastWeek[]
}

// QC Metrics
export interface QCMetricsResponse {
  period_days: number
  study_id: number | null
  total_items_processed: number
  qc_completed: number
  qc_failed: number
  first_pass_rate_percentage: number
}

// Milestone estimation
export interface SisterStudyAdjustment {
  has_sister_study: boolean
  sister_study_id: number | null
  code_reuse_percentage: number
  original_estimate: number
  adjusted_estimate: number
  reduction_percentage: number
}

export interface MilestoneEstimateResponse {
  milestone_id: number
  milestone_name: string
  remaining_items: number
  remaining_complexity: number
  team_points_per_week: number
  weeks_needed: number | null
  start_date: string
  estimated_due_date: string | null
  original_due_date: string | null
  sister_study_adjustment: SisterStudyAdjustment | null
  status?: string
  error?: string
}

