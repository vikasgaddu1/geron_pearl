import { apiClient } from '../client'
import { useAuthStore } from '@/stores/authStore'

export interface ErrorLog {
  id: number
  source: 'BACKEND' | 'FRONTEND'
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  error_type: string
  message: string
  stack_trace?: string
  request_method?: string
  request_path?: string
  request_body?: string
  response_status?: number
  user_id?: number
  user_name?: string
  user_email?: string
  ip_address?: string
  user_agent?: string
  component_name?: string
  browser_info?: string
  correlation_id?: string
  created_at: string
}

export interface ErrorLogFilters {
  source?: string
  severity?: string
  error_type?: string
  user_id?: number
  start_date?: string
  end_date?: string
  skip?: number
  limit?: number
}

export interface ErrorLogSummary {
  period_days: number
  total_errors: number
  by_severity: Record<string, number>
  by_source: Record<string, number>
  by_type: Record<string, number>
  by_day: Record<string, number>
  top_endpoints: Array<{ path: string; count: number }>
}

export interface FrontendErrorReport {
  severity?: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
  error_type: string
  message: string
  stack_trace?: string
  component_name?: string
  request_path?: string
  browser_info?: string
  correlation_id?: string
}

const BASE_PATH = '/api/v1/error-logs'

export const errorLogsApi = {
  getAll: async (filters?: ErrorLogFilters): Promise<ErrorLog[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`, { params: filters })
    return response.data
  },

  getById: async (id: number): Promise<ErrorLog> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  getSummary: async (days: number = 7): Promise<ErrorLogSummary> => {
    const response = await apiClient.get(`${BASE_PATH}/summary`, { params: { days } })
    return response.data
  },

  /**
   * Report a frontend error (public endpoint - works with or without auth)
   * Uses fetch directly to avoid axios interceptor issues during errors
   * Includes auth token if available to associate errors with users
   */
  report: async (error: FrontendErrorReport): Promise<void> => {
    try {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }

      // Include auth token if available to associate error with user
      const { tokens } = useAuthStore.getState()
      if (tokens?.accessToken) {
        headers['Authorization'] = `Bearer ${tokens.accessToken}`
      }

      await fetch(`${baseUrl}${BASE_PATH}/report`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          severity: error.severity || 'ERROR',
          error_type: error.error_type,
          message: error.message,
          stack_trace: error.stack_trace,
          component_name: error.component_name,
          request_path: error.request_path,
          browser_info: error.browser_info,
          correlation_id: error.correlation_id,
        }),
      })
    } catch {
      // Best-effort - don't throw on logging failures
      console.warn('Failed to report error to server')
    }
  },

  cleanup: async (daysToKeep: number = 30): Promise<{ logs_deleted: number; message: string }> => {
    const response = await apiClient.delete(`${BASE_PATH}/cleanup`, {
      params: { days_to_keep: daysToKeep }
    })
    return response.data
  },
}
