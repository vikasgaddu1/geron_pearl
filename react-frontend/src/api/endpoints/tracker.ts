import { apiClient } from '../client'
import type { 
  ReportingEffortItemTracker, 
  TrackerFormData, 
  BulkOperationResult,
  TrackerStatusHistory,
  TrackerPermissions,
  ProductionStatus,
  QCStatus
} from '@/types'

const BASE_PATH = '/api/v1/reporting-effort-tracker'

export interface WorkloadSummary {
  programmer_id: number
  programmer_name: string
  total_assignments: number
  production_assignments: number
  qc_assignments: number
  completed: number
  in_progress: number
  not_started: number
}

export interface BulkAssignData {
  tracker_ids: number[]
  programmer_id: number
  assignment_type: 'primary' | 'qc'
}

export interface BulkStatusUpdateData {
  tracker_ids: number[]
  status: string
  status_type: 'production' | 'qc'
}

export interface CommentWithStatusData {
  comment_text: string
  production_status?: ProductionStatus
  qc_status?: QCStatus
}

export interface CommentWithStatusResult {
  success: boolean
  comment_id: number
  status_updates: Record<string, string>
  tracker: ReportingEffortItemTracker
}

export const trackerApi = {
  getAll: async (): Promise<ReportingEffortItemTracker[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`)
    return response.data
  },

  getById: async (id: number): Promise<ReportingEffortItemTracker> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  getByItemId: async (itemId: number): Promise<ReportingEffortItemTracker | null> => {
    try {
      const response = await apiClient.get(`${BASE_PATH}/by-item/${itemId}`)
      return response.data
    } catch {
      return null
    }
  },

  getByEffortBulk: async (effortId: number): Promise<ReportingEffortItemTracker[]> => {
    const response = await apiClient.get(`${BASE_PATH}/bulk/${effortId}`)
    return response.data
  },

  create: async (data: TrackerFormData): Promise<ReportingEffortItemTracker> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  update: async (id: number, data: Partial<TrackerFormData>): Promise<ReportingEffortItemTracker> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },

  // Programmer assignment
  assignProgrammer: async (trackerId: number, data: { programmer_id: number; assignment_type: string }): Promise<ReportingEffortItemTracker> => {
    const response = await apiClient.post(`${BASE_PATH}/${trackerId}/assign-programmer`, data)
    return response.data
  },

  unassignProgrammer: async (trackerId: number, data: { assignment_type: string }): Promise<ReportingEffortItemTracker> => {
    const response = await apiClient.delete(`${BASE_PATH}/${trackerId}/unassign-programmer`, { data })
    return response.data
  },

  // Bulk operations
  bulkAssign: async (data: BulkAssignData): Promise<BulkOperationResult> => {
    const response = await apiClient.post(`${BASE_PATH}/bulk-assign`, data)
    return response.data
  },

  bulkStatusUpdate: async (data: BulkStatusUpdateData): Promise<BulkOperationResult> => {
    const response = await apiClient.post(`${BASE_PATH}/bulk-status-update`, data)
    return response.data
  },

  // Workload
  getWorkloadSummary: async (): Promise<WorkloadSummary[]> => {
    const response = await apiClient.get(`${BASE_PATH}/workload-summary`)
    return response.data
  },

  getProgrammerWorkload: async (programmerId: number): Promise<WorkloadSummary> => {
    const response = await apiClient.get(`${BASE_PATH}/workload/${programmerId}`)
    return response.data
  },

  // Export/Import
  exportData: async (effortId: number): Promise<ReportingEffortItemTracker[]> => {
    const response = await apiClient.get(`${BASE_PATH}/export/${effortId}`)
    return response.data
  },

  importData: async (effortId: number, data: unknown[], updateExisting = true): Promise<BulkOperationResult> => {
    const response = await apiClient.post(
      `${BASE_PATH}/import/${effortId}?update_existing=${updateExisting}`,
      data
    )
    return response.data
  },

  // ===== Phase 3: New Workflow Endpoints =====

  // Create a comment with optional status update (atomic operation)
  createCommentWithStatus: async (
    trackerId: number, 
    data: CommentWithStatusData
  ): Promise<CommentWithStatusResult> => {
    const response = await apiClient.post(`${BASE_PATH}/${trackerId}/comment-with-status`, data)
    return response.data
  },

  // Get status change history for time tracking
  getStatusHistory: async (
    trackerId: number, 
    statusField?: 'production' | 'qc'
  ): Promise<TrackerStatusHistory[]> => {
    const params = statusField ? `?status_field=${statusField}` : ''
    const response = await apiClient.get(`${BASE_PATH}/${trackerId}/status-history${params}`)
    return response.data
  },

  // Get current user's permissions for a tracker
  getPermissions: async (trackerId: number): Promise<TrackerPermissions> => {
    const response = await apiClient.get(`${BASE_PATH}/${trackerId}/permissions`)
    return response.data
  },

  // Update the in_production_flag
  updateProductionFlag: async (trackerId: number, value: boolean): Promise<ReportingEffortItemTracker> => {
    const response = await apiClient.put(`${BASE_PATH}/${trackerId}/production-flag?value=${value}`)
    return response.data
  },
}





