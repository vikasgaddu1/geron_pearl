/**
 * Super Admin Dashboard
 * 
 * Platform-wide statistics and tenant management.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Users,
  BookOpen,
  DollarSign,
  AlertTriangle,
  Search,
  LogOut,
  Loader2,
  Eye,
  CreditCard,
  MessageSquarePlus,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  getDashboardStats,
  getTenants,
  startImpersonation,
  superAdminLogout,
  getSuperAdminToken,
  DashboardStats,
  TenantSummary,
  getStatusBadge,
  formatMRR,
} from '@/api/endpoints/super-admin';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/api/client';
import type { User } from '@/types';
import { TenantBillingDialog } from './TenantBillingDialog';
import { FeatureRequestsKanban } from './FeatureRequestsKanban';

export function SuperAdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [tenants, setTenants] = useState<TenantSummary[]>([]);
  const [totalTenants, setTotalTenants] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [impersonating, setImpersonating] = useState<number | null>(null);
  const [billingTenant, setBillingTenant] = useState<TenantSummary | null>(null);
  const [billingDialogOpen, setBillingDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'feature-requests'>('overview');

  // Check authentication
  useEffect(() => {
    if (!getSuperAdminToken()) {
      navigate('/admin/login');
    }
  }, [navigate]);

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [statsData, tenantsData] = await Promise.all([
          getDashboardStats(),
          getTenants({ page, page_size: 10, status_filter: statusFilter || undefined, search: search || undefined }),
        ]);
        setStats(statsData);
        setTenants(tenantsData.items);
        setTotalTenants(tenantsData.total);
      } catch (error: any) {
        if (error.response?.status === 401) {
          toast.error('Session expired. Please login again.');
          navigate('/admin/login');
        } else {
          toast.error('Failed to load dashboard data');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [page, search, statusFilter, navigate]);

  const handleLogout = () => {
    superAdminLogout();
    navigate('/admin/login');
  };

  const handleOpenBilling = (tenant: TenantSummary) => {
    setBillingTenant(tenant);
    setBillingDialogOpen(true);
  };

  const handleImpersonate = async (tenant: TenantSummary) => {
    try {
      setImpersonating(tenant.id);
      const response = await startImpersonation({
        tenant_id: tenant.id,
        read_only: true,
      });

      // Store impersonation metadata
      localStorage.setItem('impersonation_tenant', tenant.display_name);
      localStorage.setItem('impersonation_tenant_id', String(tenant.id));
      localStorage.setItem('impersonation_read_only', String(response.read_only));

      // Fetch the impersonated user's info using the impersonation token
      const userResponse = await apiClient.get<User>('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${response.access_token}` },
      });

      // Set the auth store with the impersonation token and user
      // This is the proper way to authenticate - via Zustand persist
      useAuthStore.getState().login(userResponse.data, {
        accessToken: response.access_token,
        refreshToken: '', // Impersonation tokens don't have refresh tokens
      });

      toast.success(`Impersonating ${tenant.display_name} as ${userResponse.data.email}`);
      window.location.href = '/app/dashboard';
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start impersonation');
    } finally {
      setImpersonating(null);
    }
  };

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-teal-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">P</span>
              </div>
              <div>
                <h1 className="font-bold text-slate-900">Super Admin Portal</h1>
                <p className="text-xs text-slate-500">PEARL Platform Administration</p>
              </div>
            </div>
            <Button
              variant="ghost"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'overview' | 'feature-requests')} className="w-full">
          <TabsList className="mb-6 bg-slate-100 border border-slate-200">
            <TabsTrigger
              value="overview"
              className="data-[state=active]:bg-teal-600 data-[state=active]:text-white"
            >
              <Building2 className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger
              value="feature-requests"
              className="data-[state=active]:bg-teal-600 data-[state=active]:text-white"
            >
              <MessageSquarePlus className="h-4 w-4 mr-2" />
              Feature Requests
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            {/* Stats Grid */}
            {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-white border-slate-200">
              <CardHeader className="pb-2">
                <CardDescription>Total Tenants</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-teal-600" />
                  <span className="text-2xl font-bold text-slate-900">{stats.total_tenants}</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200">
              <CardHeader className="pb-2">
                <CardDescription>Active / Trialing</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-green-600" />
                  <span className="text-2xl font-bold text-slate-900">
                    {stats.active_tenants} / {stats.trialing_tenants}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200">
              <CardHeader className="pb-2">
                <CardDescription>Total Users / Studies</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-blue-600" />
                  <span className="text-2xl font-bold text-slate-900">
                    {stats.total_users} / {stats.total_studies}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200">
              <CardHeader className="pb-2">
                <CardDescription>Monthly Revenue</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-emerald-600" />
                  <span className="text-2xl font-bold text-slate-900">{formatMRR(stats.revenue_mrr)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Alerts */}
        {stats && stats.past_due_tenants > 0 && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <span className="text-red-700">
              {stats.past_due_tenants} tenant(s) have past due payments
            </span>
          </div>
        )}

        {/* Tenant List */}
        <Card className="bg-white border-slate-200">
          <CardHeader>
            <div className="flex flex-col sm:flex-row justify-between gap-4">
              <CardTitle>Tenants</CardTitle>
              <div className="flex gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Search tenants..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 w-[200px]"
                  />
                </div>
                <Select value={statusFilter || 'all'} onValueChange={(v) => setStatusFilter(v === 'all' ? '' : v)}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All statuses</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="trialing">Trialing</SelectItem>
                    <SelectItem value="past_due">Past Due</SelectItem>
                    <SelectItem value="canceled">Canceled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tenant</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-center">Users</TableHead>
                  <TableHead className="text-center">Studies</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tenants.map((tenant) => {
                  const statusBadge = getStatusBadge(tenant.subscription_status);
                  return (
                    <TableRow key={tenant.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium text-slate-900">{tenant.display_name}</div>
                          <div className="text-xs text-slate-500">{tenant.name}</div>
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-600">
                        {tenant.plan_name || '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={statusBadge.variant}>
                          {statusBadge.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center text-slate-600">
                        {tenant.users_count}
                      </TableCell>
                      <TableCell className="text-center text-slate-600">
                        {tenant.studies_count}
                      </TableCell>
                      <TableCell className="text-slate-500 text-sm">
                        {new Date(tenant.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenBilling(tenant)}
                          >
                            <CreditCard className="h-4 w-4 mr-1" />
                            Billing
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleImpersonate(tenant)}
                            disabled={impersonating === tenant.id}
                            className="text-teal-600 hover:text-teal-700"
                          >
                            {impersonating === tenant.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <>
                                <Eye className="h-4 w-4 mr-1" />
                                View
                              </>
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {tenants.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-slate-500 py-8">
                      No tenants found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>

            {/* Pagination */}
            {totalTenants > 10 && (
              <div className="flex justify-between items-center mt-4">
                <span className="text-sm text-slate-500">
                  Showing {(page - 1) * 10 + 1} to {Math.min(page * 10, totalTenants)} of {totalTenants}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={page * 10 >= totalTenants}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
          </TabsContent>

          <TabsContent value="feature-requests">
            <FeatureRequestsKanban />
          </TabsContent>
        </Tabs>
      </main>

      {/* Billing Dialog */}
      <TenantBillingDialog
        tenant={billingTenant}
        open={billingDialogOpen}
        onOpenChange={setBillingDialogOpen}
      />
    </div>
  );
}
