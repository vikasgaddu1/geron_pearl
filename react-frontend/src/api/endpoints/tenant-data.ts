/**
 * Tenant Data Management API endpoints
 */

import { apiClient } from '../client';

// =============================================================================
// Onboarding endpoints
// =============================================================================

export interface OnboardingStatus {
  onboarding_completed: boolean;
  tenant_id: number;
}

/**
 * Get onboarding status for the tenant
 */
export const getOnboardingStatus = async (): Promise<OnboardingStatus> => {
  const response = await apiClient.get<OnboardingStatus>('/tenant/onboarding/status');
  return response.data;
};

/**
 * Mark onboarding as complete
 */
export const completeOnboarding = async (): Promise<{ message: string; tenant_id: number }> => {
  const response = await apiClient.post('/tenant/onboarding/complete');
  return response.data;
};

// =============================================================================
// GDPR Data Export endpoints
// =============================================================================

/**
 * Export all tenant data as JSON (GDPR compliance)
 */
export const exportDataJson = async (): Promise<Blob> => {
  const response = await apiClient.get('/tenant/export-data', { responseType: 'blob' });
  return response.data;
};

/**
 * Export all tenant data as ZIP (GDPR compliance)
 */
export const exportDataZip = async (): Promise<Blob> => {
  const response = await apiClient.get('/tenant/export-data/zip', { responseType: 'blob' });
  return response.data;
};

/**
 * Helper to download a blob as a file
 */
export const downloadBlob = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

// =============================================================================
// Backup and Restore endpoints
// =============================================================================

export interface BackupStats {
  studies_created: number;
  database_releases_created: number;
  reporting_efforts_created: number;
  packages_created: number;
  package_items_created: number;
  text_elements_created: number;
}

/**
 * Download backup as JSON
 */
export const downloadBackup = async (): Promise<Blob> => {
  const response = await apiClient.get('/tenant/backup', { responseType: 'blob' });
  return response.data;
};

/**
 * Download backup as ZIP
 */
export const downloadBackupZip = async (): Promise<Blob> => {
  const response = await apiClient.get('/tenant/backup/zip', { responseType: 'blob' });
  return response.data;
};

/**
 * Restore from backup file
 */
export const restoreFromBackup = async (
  file: File,
  clearExisting: boolean = false
): Promise<BackupStats> => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<BackupStats>(
    `/tenant/restore?clear_existing=${clearExisting}`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
};

// =============================================================================
// Usage and Rate Limit endpoints
// =============================================================================

export interface UsageStats {
  requests_last_minute: number;
  requests_last_hour: number;
  requests_last_day: number;
  concurrent_requests: number;
}

export interface RateLimits {
  requests_per_minute: number;
  requests_per_hour: number;
  requests_per_day: number;
  max_concurrent_requests: number;
}

export interface UsageResponse {
  usage: UsageStats;
  limits: RateLimits;
  plan_name: string | null;
}

/**
 * Get current API usage statistics and rate limits
 */
export const getUsageStats = async (): Promise<UsageResponse> => {
  const response = await apiClient.get<UsageResponse>('/tenant/usage');
  return response.data;
};

// =============================================================================
// Tenant Settings endpoints
// =============================================================================

export interface SignatureLockSetting {
  signature_locks_effort: boolean;
}

/**
 * Get the signature lock setting for the tenant.
 * When true: Signing automatically locks, manual lock/unlock is hidden.
 * When false: Lock/unlock is manual and independent of signing.
 */
export const getSignatureLockSetting = async (): Promise<SignatureLockSetting> => {
  const response = await apiClient.get<SignatureLockSetting>('/tenant/settings/signature-locks-effort');
  return response.data;
};

/**
 * Update the signature lock setting for the tenant (admin only).
 */
export const updateSignatureLockSetting = async (
  signatureLocksEffort: boolean
): Promise<SignatureLockSetting> => {
  const response = await apiClient.put<SignatureLockSetting>(
    '/tenant/settings/signature-locks-effort',
    { signature_locks_effort: signatureLocksEffort }
  );
  return response.data;
};
