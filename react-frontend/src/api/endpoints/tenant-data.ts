/**
 * Tenant Data Management API endpoints
 */

import api from '../index';

// Types
export interface SampleDataStatus {
  has_sample_data: boolean;
  tenant_id: number;
}

export interface DataCounts {
  studies: number;
  database_releases: number;
  packages: number;
  package_items: number;
  text_elements: number;
  users: number;
}

export interface ResetResponse {
  message: string;
  cleared: DataCounts;
  seeded: DataCounts;
}

export interface SeedResponse {
  message: string;
  counts: DataCounts;
}

/**
 * Check if tenant has sample data seeded
 */
export const getSampleDataStatus = async (): Promise<SampleDataStatus> => {
  const response = await api.get<SampleDataStatus>('/tenant/sample-data/status');
  return response.data;
};

/**
 * Seed sample data for the tenant
 */
export const seedSampleData = async (): Promise<SeedResponse> => {
  const response = await api.post<SeedResponse>('/tenant/sample-data/seed');
  return response.data;
};

/**
 * Reset tenant data to sample state
 */
export const resetToSampleData = async (): Promise<ResetResponse> => {
  const response = await api.post<ResetResponse>('/tenant/reset-to-sample');
  return response.data;
};

/**
 * Clear all tenant data (except users)
 */
export const clearAllData = async (): Promise<DataCounts> => {
  const response = await api.delete<DataCounts>('/tenant/clear-all');
  return response.data;
};

// =============================================================================
// Onboarding endpoints
// =============================================================================

export interface OnboardingStatus {
  onboarding_completed: boolean;
  sample_data_seeded: boolean;
  tenant_id: number;
}

/**
 * Get onboarding status for the tenant
 */
export const getOnboardingStatus = async (): Promise<OnboardingStatus> => {
  const response = await api.get<OnboardingStatus>('/tenant/onboarding/status');
  return response.data;
};

/**
 * Mark onboarding as complete
 */
export const completeOnboarding = async (): Promise<{ message: string; tenant_id: number }> => {
  const response = await api.post('/tenant/onboarding/complete');
  return response.data;
};

// =============================================================================
// GDPR Data Export endpoints
// =============================================================================

/**
 * Export all tenant data as JSON (GDPR compliance)
 */
export const exportDataJson = async (): Promise<Blob> => {
  const response = await api.get('/tenant/export-data', { responseType: 'blob' });
  return response.data;
};

/**
 * Export all tenant data as ZIP (GDPR compliance)
 */
export const exportDataZip = async (): Promise<Blob> => {
  const response = await api.get('/tenant/export-data/zip', { responseType: 'blob' });
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
  const response = await api.get('/tenant/backup', { responseType: 'blob' });
  return response.data;
};

/**
 * Download backup as ZIP
 */
export const downloadBackupZip = async (): Promise<Blob> => {
  const response = await api.get('/tenant/backup/zip', { responseType: 'blob' });
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
  const response = await api.post<BackupStats>(
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
  const response = await api.get<UsageResponse>('/tenant/usage');
  return response.data;
};
