/**
 * Tenant Billing Dialog
 *
 * Shows detailed billing information for a tenant including:
 * - Stripe subscription details
 * - Usage limits and current usage
 * - Invoice history
 */

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  ExternalLink,
  Loader2,
  CreditCard,
  Users,
  BookOpen,
  Calendar,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import {
  getTenantBilling,
  TenantBillingResponse,
  TenantSummary,
  getStatusBadge,
  getInvoiceStatusBadge,
  formatCurrency,
} from '@/api/endpoints/super-admin';

interface TenantBillingDialogProps {
  tenant: TenantSummary | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TenantBillingDialog({ tenant, open, onOpenChange }: TenantBillingDialogProps) {
  const [loading, setLoading] = useState(false);
  const [billingData, setBillingData] = useState<TenantBillingResponse | null>(null);

  useEffect(() => {
    if (open && tenant) {
      fetchBillingData();
    } else {
      setBillingData(null);
    }
  }, [open, tenant?.id]);

  const fetchBillingData = async () => {
    if (!tenant) return;

    try {
      setLoading(true);
      const data = await getTenantBilling(tenant.id);
      setBillingData(data);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load billing data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const calculateUsagePercent = (current: number, limit: number): number => {
    if (limit === -1) return 0; // Unlimited
    if (limit === 0) return 100;
    return Math.min((current / limit) * 100, 100);
  };

  const getUsageLimitText = (limit: number): string => {
    return limit === -1 ? 'Unlimited' : String(limit);
  };

  if (!tenant) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-teal-600" />
            Billing Details
          </DialogTitle>
          <DialogDescription>
            {tenant.display_name} ({tenant.name})
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
          </div>
        ) : billingData ? (
          <div className="space-y-6">
            {/* Subscription Status & Stripe Link */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Badge variant={getStatusBadge(billingData.tenant.subscription_status).variant}>
                  {getStatusBadge(billingData.tenant.subscription_status).label}
                </Badge>
                {billingData.tenant.plan_name && (
                  <span className="text-slate-600">{billingData.tenant.plan_name} Plan</span>
                )}
                {billingData.tenant.cancel_at_period_end && (
                  <Badge variant="outline" className="text-orange-600 border-orange-300">
                    Canceling
                  </Badge>
                )}
              </div>
              {billingData.tenant.stripe_dashboard_url && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(billingData.tenant.stripe_dashboard_url!, '_blank')}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View in Stripe
                </Button>
              )}
            </div>

            <Separator />

            {/* Billing Period */}
            {billingData.tenant.current_period_start && billingData.tenant.current_period_end && (
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="h-4 w-4 text-slate-500" />
                  <span className="text-sm text-slate-500">Current Billing Period</span>
                </div>
                <div className="text-slate-900">
                  {formatDate(billingData.tenant.current_period_start)} - {formatDate(billingData.tenant.current_period_end)}
                </div>
              </div>
            )}

            {/* Trial Info */}
            {billingData.tenant.trial_ends_at && billingData.tenant.subscription_status === 'trialing' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-blue-600" />
                  <span className="text-blue-700">
                    Trial ends on {formatDate(billingData.tenant.trial_ends_at)}
                  </span>
                </div>
              </div>
            )}

            {/* Grace Period Warning */}
            {billingData.tenant.grace_period_ends_at && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <span className="text-red-700">
                    Grace period ends on {formatDate(billingData.tenant.grace_period_ends_at)}
                  </span>
                </div>
              </div>
            )}

            <Separator />

            {/* Usage Stats */}
            <div>
              <h4 className="text-sm font-medium text-slate-500 mb-3">Usage</h4>
              <div className="space-y-4">
                {/* Users */}
                <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-blue-600" />
                      <span className="text-slate-600">Users</span>
                    </div>
                    <span className="text-slate-900 font-medium">
                      {billingData.tenant.users_count} / {getUsageLimitText(billingData.tenant.users_limit)}
                    </span>
                  </div>
                  {billingData.tenant.users_limit !== -1 && (
                    <Progress
                      value={calculateUsagePercent(billingData.tenant.users_count, billingData.tenant.users_limit)}
                      className="h-2"
                    />
                  )}
                </div>

                {/* Studies */}
                <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4 text-green-600" />
                      <span className="text-slate-600">Studies</span>
                    </div>
                    <span className="text-slate-900 font-medium">
                      {billingData.tenant.studies_count} / {getUsageLimitText(billingData.tenant.studies_limit)}
                    </span>
                  </div>
                  {billingData.tenant.studies_limit !== -1 && (
                    <Progress
                      value={calculateUsagePercent(billingData.tenant.studies_count, billingData.tenant.studies_limit)}
                      className="h-2"
                    />
                  )}
                </div>
              </div>
            </div>

            <Separator />

            {/* Invoice History */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <FileText className="h-4 w-4 text-slate-500" />
                <h4 className="text-sm font-medium text-slate-500">Recent Invoices</h4>
              </div>

              {billingData.invoices.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invoice</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {billingData.invoices.map((invoice) => {
                      const statusBadge = getInvoiceStatusBadge(invoice.status);
                      return (
                        <TableRow key={invoice.id}>
                          <TableCell className="font-medium text-slate-900">
                            {invoice.number || invoice.id.slice(-8)}
                          </TableCell>
                          <TableCell className="text-slate-600">
                            {formatDate(invoice.created)}
                          </TableCell>
                          <TableCell>
                            <Badge variant={statusBadge.variant}>
                              {statusBadge.label}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right text-slate-900">
                            {formatCurrency(invoice.amount_due, invoice.currency)}
                          </TableCell>
                          <TableCell className="text-right">
                            {invoice.hosted_invoice_url && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => window.open(invoice.hosted_invoice_url!, '_blank')}
                              >
                                <ExternalLink className="h-3 w-3" />
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-6 text-slate-500">
                  {billingData.tenant.stripe_customer_id
                    ? 'No invoices found'
                    : 'No Stripe customer linked'}
                </div>
              )}
            </div>

            {/* Stripe IDs (for debugging/support) */}
            {(billingData.tenant.stripe_customer_id || billingData.tenant.stripe_subscription_id) && (
              <>
                <Separator />
                <div className="text-xs text-slate-500 space-y-1">
                  {billingData.tenant.stripe_customer_id && (
                    <div>Customer ID: {billingData.tenant.stripe_customer_id}</div>
                  )}
                  {billingData.tenant.stripe_subscription_id && (
                    <div>Subscription ID: {billingData.tenant.stripe_subscription_id}</div>
                  )}
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="text-center py-12 text-slate-500">
            Failed to load billing data
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
