import { apiClient } from '../client'
import type {
  AccessRequest,
  AccessRequestCreate,
  AccessRequestDeny,
  AccessRequestListResponse,
  PendingRequestCountResponse,
  AccessRequestStatus,
} from '@/types'

const BASE_PATH = '/api/v1/access-requests'

export const accessRequestsApi = {
  /**
   * Create a new access request
   */
  create: async (data: AccessRequestCreate): Promise<AccessRequest> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  /**
   * List access requests
   * @param view - 'approver' to see requests you can approve, 'requester' for your own requests
   * @param statusFilter - Optional filter by status
   */
  list: async (
    view: 'approver' | 'requester' = 'approver',
    statusFilter?: AccessRequestStatus
  ): Promise<AccessRequestListResponse> => {
    const params: Record<string, string> = { view }
    if (statusFilter) params.status_filter = statusFilter
    const response = await apiClient.get(`${BASE_PATH}/`, { params })
    return response.data
  },

  /**
   * Get count of pending requests for approvers
   */
  getPendingCount: async (): Promise<PendingRequestCountResponse> => {
    const response = await apiClient.get(`${BASE_PATH}/pending-count`)
    return response.data
  },

  /**
   * Approve an access request
   */
  approve: async (requestId: number): Promise<AccessRequest> => {
    const response = await apiClient.post(`${BASE_PATH}/${requestId}/approve`)
    return response.data
  },

  /**
   * Deny an access request
   */
  deny: async (requestId: number, data?: AccessRequestDeny): Promise<AccessRequest> => {
    const response = await apiClient.post(`${BASE_PATH}/${requestId}/deny`, data || {})
    return response.data
  },
}
