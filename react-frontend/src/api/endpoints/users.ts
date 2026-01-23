import { apiClient } from '../client'
import type { User, UserFormData, SignatureSetupResponse, SignatureStatusResponse } from '@/types'

const BASE_PATH = '/api/v1/users'

export const usersApi = {
  getAll: async (): Promise<User[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`)
    return response.data
  },

  getById: async (id: number): Promise<User> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  create: async (data: UserFormData): Promise<User> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  update: async (id: number, data: UserFormData): Promise<User> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },

  // ==================== Electronic Signature TOTP Endpoints ====================

  /**
   * Start TOTP setup for electronic signatures.
   * Returns provisioning URI for QR code and backup codes.
   */
  setupSignature: async (): Promise<SignatureSetupResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/me/signature/setup`)
    return response.data
  },

  /**
   * Verify TOTP setup with a code from the authenticator app.
   * Must be called after setupSignature to complete setup.
   */
  verifySignatureSetup: async (totpCode: string): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/me/signature/verify-setup`, {
      totp_code: totpCode,
    })
    return response.data
  },

  /**
   * Get current signature TOTP status.
   */
  getSignatureStatus: async (): Promise<SignatureStatusResponse> => {
    const response = await apiClient.get(`${BASE_PATH}/me/signature/status`)
    return response.data
  },

  /**
   * Reset/revoke TOTP and generate a new secret.
   * Invalidates old authenticator setup.
   */
  resetSignature: async (): Promise<SignatureSetupResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/me/signature/reset`)
    return response.data
  },

  /**
   * Use a one-time backup code for signing.
   */
  useSignatureBackupCode: async (backupCode: string): Promise<{ success: boolean; remaining_codes: number; message: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/me/signature/use-backup-code`, {
      backup_code: backupCode,
    })
    return response.data
  },
}

