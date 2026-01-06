import { apiClient } from '../client'
import type {
  ReportingEffortPhase,
  ReportingEffortMilestone,
  ReportingEffortMilestoneWithContext,
  PhaseFormData,
  MilestoneFormData
} from '@/types'

const BASE_PATH = '/api/v1/milestones'

// ==================== Phase API ====================

export const phasesApi = {
  /**
   * Get all phases with milestones for a reporting effort
   */
  getByReportingEffort: async (effortId: number): Promise<ReportingEffortPhase[]> => {
    const response = await apiClient.get(`${BASE_PATH}/reporting-efforts/${effortId}/phases`)
    return response.data
  },

  /**
   * Get a single phase by ID with its milestones
   */
  getById: async (phaseId: number): Promise<ReportingEffortPhase> => {
    const response = await apiClient.get(`${BASE_PATH}/phases/${phaseId}`)
    return response.data
  },

  /**
   * Create a new phase for a reporting effort
   */
  create: async (effortId: number, data: PhaseFormData): Promise<ReportingEffortPhase> => {
    const response = await apiClient.post(`${BASE_PATH}/reporting-efforts/${effortId}/phases`, {
      ...data,
      reporting_effort_id: effortId
    })
    return response.data
  },

  /**
   * Update an existing phase
   */
  update: async (phaseId: number, data: Partial<PhaseFormData>): Promise<ReportingEffortPhase> => {
    const response = await apiClient.put(`${BASE_PATH}/phases/${phaseId}`, data)
    return response.data
  },

  /**
   * Delete a phase (cascades to delete all milestones)
   */
  delete: async (phaseId: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/phases/${phaseId}`)
  },

  /**
   * Reorder phases within a reporting effort
   */
  reorder: async (effortId: number, phaseIds: number[]): Promise<ReportingEffortPhase[]> => {
    const response = await apiClient.post(
      `${BASE_PATH}/reporting-efforts/${effortId}/phases/reorder`,
      phaseIds
    )
    return response.data
  }
}

// ==================== Milestone API ====================

export const milestonesApi = {
  /**
   * Get a single milestone by ID
   */
  getById: async (milestoneId: number): Promise<ReportingEffortMilestone> => {
    const response = await apiClient.get(`${BASE_PATH}/milestones/${milestoneId}`)
    return response.data
  },

  /**
   * Create a new milestone within a phase
   */
  create: async (phaseId: number, data: MilestoneFormData): Promise<ReportingEffortMilestone> => {
    const response = await apiClient.post(`${BASE_PATH}/phases/${phaseId}/milestones`, {
      ...data,
      phase_id: phaseId
    })
    return response.data
  },

  /**
   * Update an existing milestone
   */
  update: async (milestoneId: number, data: Partial<MilestoneFormData>): Promise<ReportingEffortMilestone> => {
    const response = await apiClient.put(`${BASE_PATH}/milestones/${milestoneId}`, data)
    return response.data
  },

  /**
   * Delete a milestone
   */
  delete: async (milestoneId: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/milestones/${milestoneId}`)
  },

  /**
   * Mark a milestone as complete
   */
  markComplete: async (milestoneId: number, completionDate?: string): Promise<ReportingEffortMilestone> => {
    const response = await apiClient.post(
      `${BASE_PATH}/milestones/${milestoneId}/complete`,
      null,
      { params: completionDate ? { completion_date: completionDate } : undefined }
    )
    return response.data
  },

  /**
   * Mark a milestone as incomplete
   */
  markIncomplete: async (milestoneId: number): Promise<ReportingEffortMilestone> => {
    const response = await apiClient.post(`${BASE_PATH}/milestones/${milestoneId}/incomplete`)
    return response.data
  },

  /**
   * Reorder milestones within a phase
   */
  reorder: async (phaseId: number, milestoneIds: number[]): Promise<ReportingEffortMilestone[]> => {
    const response = await apiClient.post(
      `${BASE_PATH}/phases/${phaseId}/milestones/reorder`,
      milestoneIds
    )
    return response.data
  },

  /**
   * Get all milestones for dashboard display with full context
   */
  getForDashboard: async (params?: {
    study_id?: number
    reporting_effort_id?: number
    include_completed?: boolean
    start_date?: string
    end_date?: string
  }): Promise<ReportingEffortMilestoneWithContext[]> => {
    const response = await apiClient.get(`${BASE_PATH}/milestones/dashboard`, { params })
    return response.data
  },

  /**
   * Get upcoming milestones
   */
  getUpcoming: async (params?: {
    days_ahead?: number
    limit?: number
  }): Promise<ReportingEffortMilestoneWithContext[]> => {
    const response = await apiClient.get(`${BASE_PATH}/milestones/upcoming`, { params })
    return response.data
  },

  /**
   * Copy phases and milestones from another reporting effort
   */
  copyFromEffort: async (
    targetEffortId: number,
    sourceEffortId: number,
    dateOffsetDays?: number
  ): Promise<ReportingEffortPhase[]> => {
    const response = await apiClient.post(
      `${BASE_PATH}/reporting-efforts/${targetEffortId}/copy-from/${sourceEffortId}`,
      null,
      { params: dateOffsetDays ? { date_offset_days: dateOffsetDays } : undefined }
    )
    return response.data
  },

  /**
   * Get reporting efforts that have milestones (available as copy sources)
   */
  getAvailableSources: async (excludeEffortId?: number): Promise<Array<{
    id: number
    label: string
    study_label: string
    database_release_label: string
    phase_count: number
  }>> => {
    const response = await apiClient.get(`${BASE_PATH}/reporting-efforts/available-sources`, {
      params: excludeEffortId ? { exclude_effort_id: excludeEffortId } : undefined
    })
    return response.data
  }
}

