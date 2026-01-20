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
