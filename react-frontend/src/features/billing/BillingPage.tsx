/**
 * Billing Page for Tenant Admins
 *
 * Displays subscription status, usage statistics, and provides access
 * to Stripe Billing Portal for payment management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getBillingOverview,
  createBillingPortal,
  toggleAutoRenew,
  getStatusDisplay,
} from '@/api/endpoints/billing';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import {
  CreditCard,
  Users,
  BookOpen,
  ListChecks,
  ExternalLink,
  AlertCircle,
  Clock,
  Loader2,
  RefreshCw,
  CalendarOff,
} from 'lucide-react';

export function BillingPage() {
  const queryClient = useQueryClient();

  // Fetch billing overview
  const {
    data: billing,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['billing-overview'],
    queryFn: getBillingOverview,
  });

  // Mutation for creating portal session
  const createPortalMutation = useMutation({
    mutationFn: createBillingPortal,
    onSuccess: (data) => {
      window.open(data.url, '_blank');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to open billing portal');
    },
  });

  // Mutation for toggling auto-renewal
  const toggleAutoRenewMutation = useMutation({
    mutationFn: toggleAutoRenew,
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ['billing-overview'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update auto-renewal');
    },
  });

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

  const getStatusBadgeVariant = (
    status: string
  ): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (status) {
      case 'active':
        return 'default';
      case 'trialing':
        return 'secondary';
      case 'past_due':
      case 'unpaid':
        return 'destructive';
      case 'canceled':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return String(num);
  };

  if (isLoading) {
    return (
      <div className="flex h-[50vh] w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !billing) {
    return (
      <div className="container mx-auto py-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load billing information. Please try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const statusDisplay = getStatusDisplay(billing.subscription.status);

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <CreditCard className="h-6 w-6" />
            Billing & Subscription
          </h1>
          <p className="text-muted-foreground">
            Manage your subscription plan and view usage statistics
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Trial Warning */}
      {billing.subscription.status === 'trialing' && billing.subscription.trial_ends_at && (
        <Alert>
          <Clock className="h-4 w-4" />
          <AlertDescription>
            Your trial ends on <strong>{formatDate(billing.subscription.trial_ends_at)}</strong>.
            Add a payment method to continue using PEARL after your trial expires.
          </AlertDescription>
        </Alert>
      )}

      {/* Grace Period Warning */}
      {billing.subscription.grace_period_ends_at && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Payment issue!</strong> Your grace period ends on{' '}
            <strong>{formatDate(billing.subscription.grace_period_ends_at)}</strong>.
            Please update your payment method to avoid service interruption.
          </AlertDescription>
        </Alert>
      )}

      {/* Current Plan Card */}
      <Card>
        <CardHeader>
          <CardTitle>Your Subscription</CardTitle>
          <CardDescription>
            Current plan and subscription status
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Badge variant={getStatusBadgeVariant(billing.subscription.status)}>
                {statusDisplay.label}
              </Badge>
              <span className="text-lg font-medium">
                {billing.subscription.plan_name} Plan
              </span>
              {billing.subscription.cancel_at_period_end && (
                <Badge variant="outline" className="text-orange-500 border-orange-500">
                  Canceling at period end
                </Badge>
              )}
            </div>
          </div>

          {/* Current period info */}
          {billing.subscription.current_period_end && (
            <p className="text-sm text-muted-foreground">
              Current billing period ends on{' '}
              <strong>{formatDate(billing.subscription.current_period_end)}</strong>
            </p>
          )}

          {/* Auto-renewal toggle - only show if billing account exists */}
          {billing.has_billing_account && billing.subscription.status !== 'canceled' && (
            <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-3">
                <CalendarOff className="h-5 w-5 text-muted-foreground" />
                <div>
                  <Label htmlFor="auto-renew" className="font-medium cursor-pointer">
                    Cancel Auto-Renewal
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    {billing.subscription.cancel_at_period_end
                      ? 'Your subscription will end at the current billing period'
                      : 'Turn on to stop automatic renewal at the end of your billing period'}
                  </p>
                </div>
              </div>
              <Switch
                id="auto-renew"
                checked={billing.subscription.cancel_at_period_end}
                disabled={toggleAutoRenewMutation.isPending}
                onCheckedChange={(checked) => {
                  toggleAutoRenewMutation.mutate({ cancel_auto_renew: checked });
                }}
              />
            </div>
          )}

          {/* Manage Subscription - only show if billing account exists */}
          {billing.has_billing_account ? (
            <div className="pt-2">
              <Button
                onClick={() => createPortalMutation.mutate()}
                disabled={createPortalMutation.isPending}
              >
                {createPortalMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <ExternalLink className="h-4 w-4 mr-2" />
                )}
                Manage Subscription
              </Button>
              <p className="text-sm text-muted-foreground mt-2">
                Update payment method, view invoices, or change your plan
              </p>
            </div>
          ) : (
            <div className="pt-2 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm text-amber-800">
                <strong>Development Mode:</strong> No Stripe billing account is linked to this tenant.
                In production, tenants created through the signup flow will have full billing management.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Usage Statistics Card */}
      <Card>
        <CardHeader>
          <CardTitle>Current Usage</CardTitle>
          <CardDescription>
            Resource usage against your plan limits
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Users */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-blue-500" />
                <span className="font-medium">Users</span>
              </div>
              <span className="text-sm">
                {billing.usage.users_count} / {getUsageLimitText(billing.usage.users_limit)}
              </span>
            </div>
            {billing.usage.users_limit !== -1 && (
              <Progress
                value={calculateUsagePercent(billing.usage.users_count, billing.usage.users_limit)}
                className="h-2"
              />
            )}
            {billing.usage.users_limit !== -1 && (
              <p className="text-xs text-muted-foreground">
                {billing.usage.users_remaining} remaining
              </p>
            )}
          </div>

          {/* Studies */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="h-4 w-4 text-green-500" />
                <span className="font-medium">Studies</span>
              </div>
              <span className="text-sm">
                {billing.usage.studies_count} / {getUsageLimitText(billing.usage.studies_limit)}
              </span>
            </div>
            {billing.usage.studies_limit !== -1 && (
              <Progress
                value={calculateUsagePercent(billing.usage.studies_count, billing.usage.studies_limit)}
                className="h-2"
              />
            )}
            {billing.usage.studies_limit !== -1 && (
              <p className="text-xs text-muted-foreground">
                {billing.usage.studies_remaining} remaining
              </p>
            )}
          </div>

          {/* Tracker Items */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ListChecks className="h-4 w-4 text-purple-500" />
                <span className="font-medium">Tracker Items</span>
              </div>
              <span className="text-sm">
                {formatNumber(billing.usage.tracker_items_count)} /{' '}
                {billing.usage.tracker_items_limit === -1
                  ? 'Unlimited'
                  : formatNumber(billing.usage.tracker_items_limit)}
              </span>
            </div>
            {billing.usage.tracker_items_limit !== -1 && (
              <Progress
                value={calculateUsagePercent(
                  billing.usage.tracker_items_count,
                  billing.usage.tracker_items_limit
                )}
                className="h-2"
              />
            )}
            {billing.usage.tracker_items_limit !== -1 && (
              <p className="text-xs text-muted-foreground">
                {formatNumber(billing.usage.tracker_items_remaining)} remaining
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Upgrade Prompt */}
      {billing.upgrade_available && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">Need more capacity?</h3>
                <p className="text-sm text-muted-foreground">
                  Upgrade your plan for more users, studies, and tracker items.
                </p>
              </div>
              <Button
                variant="default"
                onClick={() => createPortalMutation.mutate()}
                disabled={createPortalMutation.isPending}
              >
                {createPortalMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : null}
                Upgrade Plan
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
