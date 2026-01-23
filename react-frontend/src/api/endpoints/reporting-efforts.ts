import { apiClient } from '../client'
import type {
  ReportingEffort,
  ReportingEffortFormData,
  LockHistoryEntry,
  SignatureHistoryEntry,
  SignatureReadinessResponse,
  SignatureVerificationResponse
} from '@/types'

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

  // ==================== Electronic Signature Endpoints ====================

  /**
   * Check if a reporting effort can be signed and what preconditions are met.
   */
  checkSignatureReadiness: async (id: number): Promise<SignatureReadinessResponse> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}/signature-readiness`)
    return response.data
  },

  /**
   * Electronically sign a reporting effort.
   * This action is PERMANENT and cannot be reversed.
   */
  sign: async (id: number, totpToken: string, reason: string): Promise<ReportingEffort> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/sign`, {
      totp_token: totpToken,
      reason: reason,
    })
    return response.data
  },

  /**
   * Get the signature history for a reporting effort.
   */
  getSignatureHistory: async (id: number): Promise<SignatureHistoryEntry[]> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}/signature-history`)
    return response.data
  },

  /**
   * Verify the integrity of a signed reporting effort.
   */
  verifySignature: async (id: number): Promise<SignatureVerificationResponse> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}/verify-signature`)
    return response.data
  },
}











