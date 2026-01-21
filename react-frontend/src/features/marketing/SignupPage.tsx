/**
 * Signup Page
 *
 * Clean clinical design - collects tenant information before redirecting to Stripe Checkout:
 * - Organization name
 * - Admin email
 * - Selected plan
 */

import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, ArrowLeft, Building2, Mail, CreditCard, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  getPlans,
  initiateSignup,
  Plan,
  formatPrice,
  getBillingStatus
} from '@/api/endpoints/billing';

// Validation schema
const signupSchema = z.object({
  tenant_name: z
    .string()
    .min(3, 'Organization name must be at least 3 characters')
    .max(50, 'Organization name must be at most 50 characters')
    .regex(
      /^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$/,
      'Organization name can only contain letters, numbers, and hyphens (no spaces)'
    ),
  email: z.string().email('Please enter a valid email address'),
  display_name: z.string().optional(),
  plan_id: z.string().min(1, 'Please select a plan'),
});

type SignupFormData = z.infer<typeof signupSchema>;

export function SignupPage() {
  const [searchParams] = useSearchParams();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stripeConfigured, setStripeConfigured] = useState(true);
  const [trialDays, setTrialDays] = useState(30);
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');

  const preselectedPlan = searchParams.get('plan');
  const preselectedBilling = searchParams.get('billing') as 'monthly' | 'yearly' | null;
  const welcomeBack = searchParams.get('welcome') === 'true';

  // Set billing period from URL param
  useEffect(() => {
    if (preselectedBilling === 'yearly') {
      setBillingPeriod('yearly');
    }
  }, [preselectedBilling]);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<SignupFormData>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      plan_id: preselectedPlan || '',
    },
  });

  const selectedPlanId = watch('plan_id');
  const selectedPlan = plans.find(p => p.id.toString() === selectedPlanId);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [plansResponse, statusResponse] = await Promise.all([
          getPlans(),
          getBillingStatus(),
        ]);
        const fetchedPlans = plansResponse?.plans ?? [];
        setPlans(fetchedPlans);
        setStripeConfigured(statusResponse?.stripe_configured ?? false);
        setTrialDays(statusResponse?.trial_days ?? 30);

        // Set default plan if not preselected
        if (!preselectedPlan && fetchedPlans.length > 0) {
          const popularPlan = fetchedPlans.find(p => p.is_popular);
          const defaultPlan = popularPlan || fetchedPlans[0];
          setValue('plan_id', defaultPlan.id.toString());
        }
      } catch (err) {
        console.error('Failed to fetch signup data:', err);
        setError('Failed to load plans. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [preselectedPlan, setValue]);

  const onSubmit = async (data: SignupFormData) => {
    setSubmitting(true);
    setError(null);

    try {
      const response = await initiateSignup({
        tenant_name: data.tenant_name.toLowerCase().replace(/\s+/g, '-'),
        email: data.email,
        plan_id: parseInt(data.plan_id),
        display_name: data.display_name || undefined,
        billing_period: billingPeriod,
      });

      // Redirect to Stripe Checkout
      window.location.href = response.checkout_url;
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        'Failed to start signup. Please try again.'
      );
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Navigation */}
      <nav className="border-b border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-9 h-9 bg-teal-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">P</span>
              </div>
              <span className="font-semibold text-xl text-slate-900 tracking-tight">PEARL</span>
            </Link>
            <Link
              to="/pricing"
              className="text-slate-600 hover:text-slate-900 font-medium text-sm flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Pricing
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-md mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">
            Create your account
          </h1>
          <p className="text-slate-600 text-sm">
            Start your {trialDays}-day free trial. No credit card required to start.
          </p>
        </div>

        {/* Welcome Back Alert */}
        {welcomeBack && (
          <Alert className="mb-6 bg-teal-50 border-teal-200">
            <CheckCircle className="h-4 w-4 text-teal-600" />
            <AlertDescription className="text-teal-800">
              Welcome to PEARL! Check your email for login instructions.
            </AlertDescription>
          </Alert>
        )}

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Stripe Not Configured Warning */}
        {!stripeConfigured && (
          <Alert className="mb-6 border-slate-200">
            <AlertDescription>
              Payment processing is not configured. Please contact support to set up your account.
            </AlertDescription>
          </Alert>
        )}

        {/* No Plans Available Warning */}
        {plans.length === 0 && !error && (
          <Alert className="mb-6 border-slate-200">
            <AlertDescription>
              No subscription plans are currently available. Please contact support or try again later.
            </AlertDescription>
          </Alert>
        )}

        {/* Signup Form */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Organization Name */}
            <div className="space-y-1.5">
              <Label htmlFor="tenant_name" className="flex items-center gap-2 text-sm">
                <Building2 className="h-4 w-4 text-slate-400" />
                Organization Name
              </Label>
              <Input
                id="tenant_name"
                placeholder="acme-pharma"
                {...register('tenant_name')}
                className={`${errors.tenant_name ? 'border-red-500' : 'border-slate-200'}`}
              />
              {errors.tenant_name && (
                <p className="text-xs text-red-500">{errors.tenant_name.message}</p>
              )}
              <p className="text-xs text-slate-500">
                This will be used in your workspace URL
              </p>
            </div>

            {/* Display Name (Optional) */}
            <div className="space-y-1.5">
              <Label htmlFor="display_name" className="text-sm">
                Display Name <span className="text-slate-400">(optional)</span>
              </Label>
              <Input
                id="display_name"
                placeholder="ACME Pharma Inc."
                {...register('display_name')}
                className="border-slate-200"
              />
            </div>

            {/* Email */}
            <div className="space-y-1.5">
              <Label htmlFor="email" className="flex items-center gap-2 text-sm">
                <Mail className="h-4 w-4 text-slate-400" />
                Admin Email
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@acme-pharma.com"
                {...register('email')}
                className={`${errors.email ? 'border-red-500' : 'border-slate-200'}`}
              />
              {errors.email && (
                <p className="text-xs text-red-500">{errors.email.message}</p>
              )}
              <p className="text-xs text-slate-500">
                We'll send your login credentials here
              </p>
            </div>

            {/* Billing Period Toggle */}
            <div className="space-y-1.5">
              <Label className="text-sm">Billing Period</Label>
              <div className="inline-flex items-center bg-slate-100 rounded-lg p-1 w-full">
                <button
                  type="button"
                  onClick={() => setBillingPeriod('monthly')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                    billingPeriod === 'monthly'
                      ? 'bg-white shadow text-slate-900'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Monthly
                </button>
                <button
                  type="button"
                  onClick={() => setBillingPeriod('yearly')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                    billingPeriod === 'yearly'
                      ? 'bg-white shadow text-slate-900'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Yearly
                  <Badge variant="secondary" className="bg-teal-100 text-teal-700 border-0 text-xs">
                    Save 17%
                  </Badge>
                </button>
              </div>
            </div>

            {/* Plan Selection */}
            <div className="space-y-1.5">
              <Label htmlFor="plan_id" className="flex items-center gap-2 text-sm">
                <CreditCard className="h-4 w-4 text-slate-400" />
                Select Plan
              </Label>
              <Select
                value={selectedPlanId}
                onValueChange={(value) => setValue('plan_id', value)}
              >
                <SelectTrigger className={`${errors.plan_id ? 'border-red-500' : 'border-slate-200'}`}>
                  <SelectValue placeholder="Choose a plan" />
                </SelectTrigger>
                <SelectContent>
                  {plans
                    .filter(p => p.price_monthly > 0)
                    .map((plan) => (
                      <SelectItem key={plan.id} value={plan.id.toString()}>
                        {plan.display_name} - {billingPeriod === 'yearly' && plan.price_yearly
                          ? `$${(plan.price_yearly / 100 / 12).toFixed(0)}/mo`
                          : formatPrice(plan.price_monthly) + '/mo'}
                        {plan.is_popular && ' (Popular)'}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              {errors.plan_id && (
                <p className="text-xs text-red-500">{errors.plan_id.message}</p>
              )}
            </div>

            {/* Selected Plan Summary */}
            {selectedPlan && (
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium text-slate-900 text-sm">{selectedPlan.display_name}</span>
                  <div className="text-right">
                    {billingPeriod === 'yearly' && selectedPlan.price_yearly ? (
                      <>
                        <span className="font-semibold text-teal-600">
                          ${(selectedPlan.price_yearly / 100 / 12).toFixed(0)}/month
                        </span>
                        <span className="text-xs text-slate-500 block">
                          billed ${(selectedPlan.price_yearly / 100).toFixed(0)}/year
                        </span>
                      </>
                    ) : (
                      <span className="font-semibold text-teal-600">
                        {formatPrice(selectedPlan.price_monthly)}/month
                      </span>
                    )}
                  </div>
                </div>
                <ul className="text-xs text-slate-600 space-y-1">
                  <li>• {selectedPlan.max_users === -1 ? 'Unlimited' : selectedPlan.max_users} users</li>
                  <li>• {selectedPlan.max_studies === -1 ? 'Unlimited' : selectedPlan.max_studies} studies</li>
                  <li>• {trialDays}-day free trial</li>
                  {billingPeriod === 'yearly' && (
                    <li className="text-teal-600 font-medium">• 2 months free (17% savings)</li>
                  )}
                </ul>
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              size="lg"
              className="w-full bg-teal-600 hover:bg-teal-700 text-white font-medium"
              disabled={submitting || !stripeConfigured || plans.length === 0}
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Setting up your account...
                </>
              ) : (
                'Continue to Payment'
              )}
            </Button>

            {/* Terms */}
            <p className="text-xs text-center text-slate-500">
              By signing up, you agree to our{' '}
              <Link to="/terms" className="text-teal-600 hover:underline">Terms of Service</Link>
              {' '}and{' '}
              <Link to="/privacy" className="text-teal-600 hover:underline">Privacy Policy</Link>
            </p>
          </form>
        </div>

        {/* Already have account */}
        <div className="mt-6 text-center">
          <p className="text-slate-600 text-sm">
            Already have an account?{' '}
            <Link to="/app/login" className="text-teal-600 font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
