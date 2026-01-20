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
  UserCog,
  LogOut,
  Loader2,
  Eye,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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

  const handleImpersonate = async (tenant: TenantSummary) => {
    try {
      setImpersonating(tenant.id);
      const response = await startImpersonation({
        tenant_id: tenant.id,
        read_only: true,
      });
      
      // Store impersonation token in regular auth storage
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('impersonation_tenant', tenant.display_name);
      localStorage.setItem('impersonation_read_only', String(response.read_only));
      
      toast.success(`Impersonating ${tenant.display_name}`);
      window.location.href = '/app/dashboard';
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start impersonation');
    } finally {
      setImpersonating(null);
    }
  };

  if (loading && !stats) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-800/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center">
                <UserCog className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-white">Super Admin Portal</h1>
                <p className="text-xs text-slate-400">PEARL Platform Administration</p>
              </div>
            </div>
            <Button 
              variant="ghost" 
              onClick={handleLogout}
              className="text-slate-400 hover:text-white hover:bg-slate-700"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardDescription className="text-slate-400">Total Tenants</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-amber-500" />
                  <span className="text-2xl font-bold text-white">{stats.total_tenants}</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardDescription className="text-slate-400">Active / Trialing</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-green-500" />
                  <span className="text-2xl font-bold text-white">
                    {stats.active_tenants} / {stats.trialing_tenants}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardDescription className="text-slate-400">Total Users / Studies</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-blue-500" />
                  <span className="text-2xl font-bold text-white">
                    {stats.total_users} / {stats.total_studies}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800 border-slate-700">
              <CardHeader className="pb-2">
                <CardDescription className="text-slate-400">Monthly Revenue</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-emerald-500" />
                  <span className="text-2xl font-bold text-white">{formatMRR(stats.revenue_mrr)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Alerts */}
        {stats && stats.past_due_tenants > 0 && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-800 rounded-lg flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            <span className="text-red-300">
              {stats.past_due_tenants} tenant(s) have past due payments
            </span>
          </div>
        )}

        {/* Tenant List */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <div className="flex flex-col sm:flex-row justify-between gap-4">
              <CardTitle className="text-white">Tenants</CardTitle>
              <div className="flex gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Search tenants..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 bg-slate-700 border-slate-600 text-white placeholder:text-slate-500 w-[200px]"
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[140px] bg-slate-700 border-slate-600 text-white">
                    <SelectValue placeholder="All statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All statuses</SelectItem>
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
                <TableRow className="border-slate-700 hover:bg-slate-700/50">
                  <TableHead className="text-slate-400">Tenant</TableHead>
                  <TableHead className="text-slate-400">Plan</TableHead>
                  <TableHead className="text-slate-400">Status</TableHead>
                  <TableHead className="text-slate-400 text-center">Users</TableHead>
                  <TableHead className="text-slate-400 text-center">Studies</TableHead>
                  <TableHead className="text-slate-400">Created</TableHead>
                  <TableHead className="text-slate-400 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tenants.map((tenant) => {
                  const statusBadge = getStatusBadge(tenant.subscription_status);
                  return (
                    <TableRow key={tenant.id} className="border-slate-700 hover:bg-slate-700/50">
                      <TableCell>
                        <div>
                          <div className="font-medium text-white">{tenant.display_name}</div>
                          <div className="text-xs text-slate-500">{tenant.name}</div>
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-300">
                        {tenant.plan_name || '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={statusBadge.variant}>
                          {statusBadge.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center text-slate-300">
                        {tenant.users_count}
                      </TableCell>
                      <TableCell className="text-center text-slate-300">
                        {tenant.studies_count}
                      </TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {new Date(tenant.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleImpersonate(tenant)}
                          disabled={impersonating === tenant.id}
                          className="text-amber-500 hover:text-amber-400 hover:bg-slate-700"
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
                <span className="text-sm text-slate-400">
                  Showing {(page - 1) * 10 + 1} to {Math.min(page * 10, totalTenants)} of {totalTenants}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="border-slate-600 text-slate-300 hover:bg-slate-700"
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={page * 10 >= totalTenants}
                    className="border-slate-600 text-slate-300 hover:bg-slate-700"
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
