import { apiClient } from '../client'
import type { AuditLog, AuditLogFilters, AuditLogSummary } from '@/types'

const BASE_PATH = '/api/v1/audit-trail'

export const auditLogsApi = {
  getAll: async (filters?: AuditLogFilters): Promise<AuditLog[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`, { params: filters })
    return response.data
  },

  getSummary: async (days: number = 7): Promise<AuditLogSummary> => {
    const response = await apiClient.get(`${BASE_PATH}/summary`, { params: { days } })
    return response.data
  },

  getRecordHistory: async (tableName: string, recordId: number): Promise<AuditLog[]> => {
    const response = await apiClient.get(`${BASE_PATH}/record/${tableName}/${recordId}`)
    return response.data
  },
}
