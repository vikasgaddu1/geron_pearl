/**
 * Super Admin API endpoints
 */

import { apiClient } from '../client';

const BASE_PATH = '/api/v1/super-admin';

// Types
export interface SuperAdmin {
  id: number;
  email: string;
  name: string;
  is_active: boolean;
  mfa_enabled: boolean;
  last_login_at: string | null;
  last_login_ip: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface SuperAdminLoginRequest {
  email: string;
  password: string;
  mfa_token?: string;
}

export interface SuperAdminLoginResponse {
  access_token: string;
  token_type: string;
  requires_mfa: boolean;
  super_admin: SuperAdmin;
}

export interface MFASetupResponse {
  secret: string;
  provisioning_uri: string;
  backup_codes: string[];
}

export interface ImpersonationRequest {
  tenant_id: number;
  target_user_id?: number;
  read_only?: boolean;
}

export interface ImpersonationResponse {
  access_token: string;
  token_type: string;
  tenant_id: number;
  tenant_name: string;
  target_user_id: number;
  target_username: string;
  read_only: boolean;
  expires_at: string;
}

export interface TenantSummary {
  id: number;
  name: string;
  display_name: string;
  subscription_status: string;
  plan_name: string | null;
  users_count: number;
  studies_count: number;
  created_at: string;
  trial_ends_at: string | null;
  is_deleted: boolean;
}

export interface TenantListResponse {
  items: TenantSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardStats {
  total_tenants: number;
  active_tenants: number;
  trialing_tenants: number;
  past_due_tenants: number;
  canceled_tenants: number;
  total_users: number;
  total_studies: number;
  revenue_mrr: number;
}

// Billing Types
export interface TenantBillingDetails {
  id: number;
  name: string;
  display_name: string;
  created_at: string;
  stripe_customer_id: string | null;
  stripe_subscription_id: string | null;
  stripe_dashboard_url: string | null;
  subscription_status: string;
  plan_name: string | null;
  plan_id: number | null;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  trial_ends_at: string | null;
  grace_period_ends_at: string | null;
  users_count: number;
  users_limit: number;
  studies_count: number;
  studies_limit: number;
}

export interface InvoiceSummary {
  id: string;
  number: string | null;
  status: string;
  amount_due: number;
  amount_paid: number;
  currency: string;
  created: string;
  due_date: string | null;
  paid_at: string | null;
  invoice_pdf: string | null;
  hosted_invoice_url: string | null;
}

export interface TenantBillingResponse {
  tenant: TenantBillingDetails;
  invoices: InvoiceSummary[];
}

export interface RevenueByPlan {
  plan_name: string;
  plan_id: number;
  tenant_count: number;
  mrr: number;
}

export interface RevenueStats {
  total_mrr: number;
  by_plan: RevenueByPlan[];
  trial_count: number;
  trial_conversion_rate: number | null;
  churned_last_30_days: number;
}

// Super admin token storage
// Using sessionStorage for enhanced security - token doesn't persist across browser sessions
const SUPER_ADMIN_TOKEN_KEY = 'super_admin_token';

export const setSuperAdminToken = (token: string) => {
  // Use sessionStorage for super admin tokens (more secure than localStorage)
  sessionStorage.setItem(SUPER_ADMIN_TOKEN_KEY, token);
};

export const getSuperAdminToken = (): string | null => {
  return sessionStorage.getItem(SUPER_ADMIN_TOKEN_KEY);
};

export const clearSuperAdminToken = () => {
  sessionStorage.removeItem(SUPER_ADMIN_TOKEN_KEY);
};

// Helper to get auth header for super admin
const getSuperAdminAuthHeader = () => {
  const token = getSuperAdminToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// API Functions

/**
 * Super admin login
 */
export const superAdminLogin = async (data: SuperAdminLoginRequest): Promise<SuperAdminLoginResponse> => {
  const response = await apiClient.post<SuperAdminLoginResponse>(`${BASE_PATH}/login`, data);
  if (response.data.access_token && !response.data.requires_mfa) {
    setSuperAdminToken(response.data.access_token);
  }
  return response.data;
};

/**
 * Get current super admin profile
 */
export const getSuperAdminMe = async (): Promise<SuperAdmin> => {
  const response = await apiClient.get<SuperAdmin>(`${BASE_PATH}/me`, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Setup MFA for super admin
 */
export const setupMFA = async (): Promise<MFASetupResponse> => {
  const response = await apiClient.post<MFASetupResponse>(`${BASE_PATH}/mfa/setup`, {}, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Verify MFA setup
 */
export const verifyMFA = async (token: string): Promise<{ message: string }> => {
  const response = await apiClient.post(`${BASE_PATH}/mfa/verify`, { token }, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Get dashboard statistics
 */
export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await apiClient.get<DashboardStats>(`${BASE_PATH}/dashboard/stats`, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Get list of tenants
 */
export const getTenants = async (params?: {
  page?: number;
  page_size?: number;
  status_filter?: string;
  search?: string;
}): Promise<TenantListResponse> => {
  const response = await apiClient.get<TenantListResponse>(`${BASE_PATH}/tenants`, {
    params,
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Get a specific tenant
 */
export const getTenant = async (tenantId: number): Promise<TenantSummary> => {
  const response = await apiClient.get<TenantSummary>(`${BASE_PATH}/tenants/${tenantId}`, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Start impersonation session
 */
export const startImpersonation = async (data: ImpersonationRequest): Promise<ImpersonationResponse> => {
  const response = await apiClient.post<ImpersonationResponse>(`${BASE_PATH}/impersonate`, data, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * End impersonation session (for audit logging)
 */
export const endImpersonation = async (tenantId?: number): Promise<{ message: string }> => {
  const response = await apiClient.post(`${BASE_PATH}/impersonate/end`, 
    tenantId ? { tenant_id: tenantId } : {},
    { headers: getSuperAdminAuthHeader() }
  );
  return response.data;
};

/**
 * Logout super admin
 */
export const superAdminLogout = () => {
  clearSuperAdminToken();
};

// Helper functions

/**
 * Format subscription status for display
 */
export const getStatusBadge = (status: string): { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' } => {
  switch (status) {
    case 'active':
      return { label: 'Active', variant: 'default' };
    case 'trialing':
      return { label: 'Trial', variant: 'secondary' };
    case 'past_due':
      return { label: 'Past Due', variant: 'destructive' };
    case 'canceled':
      return { label: 'Canceled', variant: 'outline' };
    case 'unpaid':
      return { label: 'Unpaid', variant: 'destructive' };
    default:
      return { label: status, variant: 'secondary' };
  }
};

/**
 * Format MRR for display
 */
export const formatMRR = (cents: number): string => {
  return `$${(cents / 100).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

/**
 * Format currency amount in cents for display
 */
export const formatCurrency = (cents: number, currency: string = 'usd'): string => {
  const amount = cents / 100;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
    minimumFractionDigits: 2,
  }).format(amount);
};

/**
 * Get invoice status badge styling
 */
export const getInvoiceStatusBadge = (status: string): { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' } => {
  switch (status) {
    case 'paid':
      return { label: 'Paid', variant: 'default' };
    case 'open':
      return { label: 'Open', variant: 'secondary' };
    case 'draft':
      return { label: 'Draft', variant: 'outline' };
    case 'void':
      return { label: 'Void', variant: 'outline' };
    case 'uncollectible':
      return { label: 'Uncollectible', variant: 'destructive' };
    default:
      return { label: status, variant: 'secondary' };
  }
};

// Billing API Functions

/**
 * Get detailed billing information for a tenant
 */
export const getTenantBilling = async (tenantId: number): Promise<TenantBillingResponse> => {
  const response = await apiClient.get<TenantBillingResponse>(`${BASE_PATH}/tenants/${tenantId}/billing`, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Get revenue breakdown by plan
 */
export const getRevenueBreakdown = async (): Promise<RevenueStats> => {
  const response = await apiClient.get<RevenueStats>(`${BASE_PATH}/revenue/breakdown`, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

// Feature Request Types
export interface FeatureRequestWithUser {
  id: number;
  tenant_id: number;
  user_id: number;
  category: 'bug' | 'feature';
  title: string;
  description: string;
  status: 'pending' | 'working' | 'done';
  admin_response?: string;
  responded_at?: string;
  created_at: string;
  updated_at: string;
  user_name?: string;
  user_email?: string;
  tenant_name?: string;
}

export interface FeatureRequestListResponse {
  items: FeatureRequestWithUser[];
  total: number;
  skip: number;
  limit: number;
}

export interface FeatureRequestStats {
  pending: number;
  working: number;
  done: number;
  total: number;
}

export interface FeatureRequestUpdate {
  status?: 'pending' | 'working' | 'done';
  admin_response?: string;
}

// Feature Request API Functions

/**
 * Get all feature requests across all tenants
 */
export const getFeatureRequests = async (params?: {
  skip?: number;
  limit?: number;
  status_filter?: string;
  category_filter?: string;
}): Promise<FeatureRequestListResponse> => {
  const response = await apiClient.get<FeatureRequestListResponse>(`${BASE_PATH}/feature-requests`, {
    params,
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Get feature request statistics
 */
export const getFeatureRequestStats = async (): Promise<FeatureRequestStats> => {
  const response = await apiClient.get<FeatureRequestStats>(`${BASE_PATH}/feature-requests/stats`, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Get a specific feature request
 */
export const getFeatureRequest = async (requestId: number): Promise<FeatureRequestWithUser> => {
  const response = await apiClient.get<FeatureRequestWithUser>(`${BASE_PATH}/feature-requests/${requestId}`, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Update a feature request (status and/or admin response)
 */
export const updateFeatureRequest = async (
  requestId: number,
  data: FeatureRequestUpdate
): Promise<FeatureRequestWithUser> => {
  const response = await apiClient.put<FeatureRequestWithUser>(
    `${BASE_PATH}/feature-requests/${requestId}`,
    data,
    { headers: getSuperAdminAuthHeader() }
  );
  return response.data;
};

/**
 * Get feature request status badge styling
 */
export const getFeatureRequestStatusBadge = (status: string): { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; color: string } => {
  switch (status) {
    case 'pending':
      return { label: 'Pending', variant: 'secondary', color: 'amber' };
    case 'working':
      return { label: 'Working', variant: 'default', color: 'blue' };
    case 'done':
      return { label: 'Done', variant: 'outline', color: 'green' };
    default:
      return { label: status, variant: 'secondary', color: 'gray' };
  }
};

/**
 * Get feature request category badge styling
 */
export const getFeatureRequestCategoryBadge = (category: string): { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: string } => {
  switch (category) {
    case 'bug':
      return { label: 'Bug', variant: 'destructive', icon: 'bug' };
    case 'feature':
      return { label: 'Feature', variant: 'secondary', icon: 'lightbulb' };
    default:
      return { label: category, variant: 'secondary', icon: 'help' };
  }
};
