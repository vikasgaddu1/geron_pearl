import { apiClient } from '../client'
import type { ReportingEffort, ReportingEffortFormData, LockHistoryEntry } from '@/types'

const BASE_PATH = '/api/v1/reporting-efforts'

export const reportingEffortsApi = {
  getAll: async (): Promise<ReportingEffort[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`)
    return response.data
  },

  getById: async (id: number): Promise<ReportingEffort> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  getByReleaseId: async (releaseId: number): Promise<ReportingEffort[]> => {
    const response = await apiClient.get(`${BASE_PATH}/?database_release_id=${releaseId}`)
    return response.data
  },

  create: async (data: ReportingEffortFormData): Promise<ReportingEffort> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  update: async (id: number, data: Partial<ReportingEffortFormData>): Promise<ReportingEffort> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },

  // Lock/Unlock operations
  lock: async (id: number, reason: string): Promise<ReportingEffort> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/lock`, { reason })
    return response.data
  },

  unlock: async (id: number, reason: string): Promise<ReportingEffort> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/unlock`, { reason })
    return response.data
  },

  getLockHistory: async (id: number): Promise<LockHistoryEntry[]> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}/lock-history`)
    return response.data
  },
}











