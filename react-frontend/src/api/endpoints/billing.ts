/**
 * Billing API endpoints for subscription management
 */

import { apiClient } from '../client';

// Types
export interface Plan {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  price_monthly: number;
  price_yearly: number | null;
  max_users: number;
  max_studies: number;
  max_tracker_items: number;
  features: Record<string, boolean> | null;
  is_popular: boolean;
}

export interface PlansResponse {
  plans: Plan[];
}

export interface SignupInitiateRequest {
  tenant_name: string;
  email: string;
  plan_id: number;
  display_name?: string;
  billing_period?: 'monthly' | 'yearly';
}

export interface SignupInitiateResponse {
  checkout_url: string;
  session_id: string;
}

export interface SubscriptionInfo {
  status: 'trialing' | 'active' | 'past_due' | 'canceled' | 'unpaid';
  plan_name: string;
  plan_id: number;
  current_period_end: string | null;
  trial_ends_at: string | null;
  grace_period_ends_at: string | null;
  cancel_at_period_end: boolean;
}

export interface UsageInfo {
  users_count: number;
  users_limit: number;
  users_remaining: number;
  studies_count: number;
  studies_limit: number;
  studies_remaining: number;
  tracker_items_count: number;
  tracker_items_limit: number;
  tracker_items_remaining: number;
}

export interface BillingOverview {
  subscription: SubscriptionInfo;
  usage: UsageInfo;
  can_add_users: boolean;
  can_add_studies: boolean;
  upgrade_available: boolean;
  has_billing_account: boolean;
}

export interface BillingPortalResponse {
  url: string;
}

export interface BillingStatus {
  stripe_configured: boolean;
  trial_days: number;
  grace_period_days: number;
}

export interface AutoRenewRequest {
  cancel_auto_renew: boolean;
}

export interface AutoRenewResponse {
  cancel_at_period_end: boolean;
  current_period_end: string | null;
  message: string;
}

// API Functions

/**
 * Get list of available subscription plans (public)
 */
export const getPlans = async (): Promise<PlansResponse> => {
  const response = await apiClient.get<PlansResponse>('/api/v1/billing/plans');
  return response.data;
};

/**
 * Initiate signup - creates Stripe Checkout session (public)
 */
export const initiateSignup = async (data: SignupInitiateRequest): Promise<SignupInitiateResponse> => {
  const response = await apiClient.post<SignupInitiateResponse>('/api/v1/billing/signup/initiate', data);
  return response.data;
};

/**
 * Get billing overview for current tenant (authenticated)
 */
export const getBillingOverview = async (): Promise<BillingOverview> => {
  const response = await apiClient.get<BillingOverview>('/api/v1/billing/overview');
  return response.data;
};

/**
 * Create Stripe Billing Portal session (admin only)
 */
export const createBillingPortal = async (): Promise<BillingPortalResponse> => {
  const response = await apiClient.post<BillingPortalResponse>('/api/v1/billing/portal');
  return response.data;
};

/**
 * Check if Stripe is configured (public)
 */
export const getBillingStatus = async (): Promise<BillingStatus> => {
  const response = await apiClient.get<BillingStatus>('/api/v1/billing/status');
  return response.data;
};

/**
 * Toggle auto-renewal for subscription (admin only)
 */
export const toggleAutoRenew = async (data: AutoRenewRequest): Promise<AutoRenewResponse> => {
  const response = await apiClient.post<AutoRenewResponse>('/api/v1/billing/auto-renew', data);
  return response.data;
};

// Helper functions

/**
 * Format price in cents to display string
 */
export const formatPrice = (cents: number): string => {
  if (cents === 0) return 'Custom';
  return `$${(cents / 100).toFixed(0)}`;
};

/**
 * Get subscription status display info
 */
export const getStatusDisplay = (status: SubscriptionInfo['status']): { label: string; color: string } => {
  switch (status) {
    case 'active':
      return { label: 'Active', color: 'text-green-600' };
    case 'trialing':
      return { label: 'Trial', color: 'text-blue-600' };
    case 'past_due':
      return { label: 'Payment Due', color: 'text-yellow-600' };
    case 'canceled':
      return { label: 'Canceled', color: 'text-gray-500' };
    case 'unpaid':
      return { label: 'Unpaid', color: 'text-red-600' };
    default:
      return { label: status, color: 'text-gray-600' };
  }
};
