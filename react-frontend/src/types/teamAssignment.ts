/**
 * Team Assignment types
 */

export type JobType = 'LEAD' | 'PRODUCTION_PROGRAMMER' | 'QC_PROGRAMMER'
export type ExperienceLevel = 'JUNIOR' | 'MID' | 'SENIOR'
export type DepartureReason = 'left_organization' | 'reassigned_fully' | 'allocation_changed' | 'project_ended'

export interface StudyTeamAssignment {
  id: number
  user_id: number
  study_id: number
  job_type: JobType
  allocation_percentage: number
  productive_time_factor: number
  experience_level: ExperienceLevel
  effective_start_date: string
  effective_end_date: string | null
  is_active: boolean
  departure_reason: DepartureReason | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface TeamMemberSummary {
  user_id: number
  username: string
  email: string
  job_type: JobType
  allocation_percentage: number
  productive_time_factor: number
  experience_level: ExperienceLevel
  effective_start_date: string
  is_active: boolean
  effective_weekly_hours: number
  assignment_id: number
}

export interface StudyTeamResponse {
  study_id: number
  study_label: string
  active_members: TeamMemberSummary[]
  total_allocation_percentage: number
  total_weekly_capacity_hours: number
  member_count: number
}

export interface CreateTeamAssignmentRequest {
  user_id: number
  job_type: JobType
  allocation_percentage: number
  productive_time_factor: number
  experience_level: ExperienceLevel
  effective_start_date: string
  notes?: string
}

export interface ChangeAllocationRequest {
  new_allocation_percentage: number
  new_productive_time_factor?: number
  new_experience_level?: ExperienceLevel
  new_job_type?: JobType
  effective_date?: string
  notes?: string
}

export interface EndAssignmentRequest {
  effective_date?: string
  departure_reason: DepartureReason
  notes?: string
}

export interface AllocationHistoryResponse {
  user_id: number
  username: string
  study_id: number
  study_label: string
  assignments: StudyTeamAssignment[]
}

