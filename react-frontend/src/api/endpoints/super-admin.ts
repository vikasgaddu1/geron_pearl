/**
 * Super Admin API endpoints
 */

import api from '../index';

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

// Create a separate axios instance for super admin (different token storage)
const SUPER_ADMIN_TOKEN_KEY = 'super_admin_token';

export const setSuperAdminToken = (token: string) => {
  localStorage.setItem(SUPER_ADMIN_TOKEN_KEY, token);
};

export const getSuperAdminToken = (): string | null => {
  return localStorage.getItem(SUPER_ADMIN_TOKEN_KEY);
};

export const clearSuperAdminToken = () => {
  localStorage.removeItem(SUPER_ADMIN_TOKEN_KEY);
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
  const response = await api.post<SuperAdminLoginResponse>('/super-admin/login', data);
  if (response.data.access_token && !response.data.requires_mfa) {
    setSuperAdminToken(response.data.access_token);
  }
  return response.data;
};

/**
 * Get current super admin profile
 */
export const getSuperAdminMe = async (): Promise<SuperAdmin> => {
  const response = await api.get<SuperAdmin>('/super-admin/me', {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Setup MFA for super admin
 */
export const setupMFA = async (): Promise<MFASetupResponse> => {
  const response = await api.post<MFASetupResponse>('/super-admin/mfa/setup', {}, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Verify MFA setup
 */
export const verifyMFA = async (token: string): Promise<{ message: string }> => {
  const response = await api.post('/super-admin/mfa/verify', { token }, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Get dashboard statistics
 */
export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await api.get<DashboardStats>('/super-admin/dashboard/stats', {
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
  const response = await api.get<TenantListResponse>('/super-admin/tenants', {
    params,
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Get a specific tenant
 */
export const getTenant = async (tenantId: number): Promise<TenantSummary> => {
  const response = await api.get<TenantSummary>(`/super-admin/tenants/${tenantId}`, {
    headers: getSuperAdminAuthHeader(),
  });
  return response.data;
};

/**
 * Start impersonation session
 */
export const startImpersonation = async (data: ImpersonationRequest): Promise<ImpersonationResponse> => {
  const response = await api.post<ImpersonationResponse>('/super-admin/impersonate', data, {
    headers: getSuperAdminAuthHeader(),
  });
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
