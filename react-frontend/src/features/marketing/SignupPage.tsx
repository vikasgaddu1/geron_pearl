/**
 * Signup Page
 * 
 * Collects tenant information before redirecting to Stripe Checkout:
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

  const preselectedPlan = searchParams.get('plan');
  const welcomeBack = searchParams.get('welcome') === 'true';

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
        // Defensive: handle cases where plans might be undefined or not an array
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-50 to-white">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">P</span>
              </div>
              <span className="font-bold text-xl text-gray-900">PEARL</span>
            </Link>
            <Link 
              to="/pricing" 
              className="text-gray-600 hover:text-gray-900 font-medium flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Pricing
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-xl mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Create your account
          </h1>
          <p className="text-gray-600">
            Start your {trialDays}-day free trial. No credit card required to start.
          </p>
        </div>

        {/* Welcome Back Alert */}
        {welcomeBack && (
          <Alert className="mb-6 bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
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
          <Alert className="mb-6">
            <AlertDescription>
              Payment processing is not configured. Please contact support to set up your account.
            </AlertDescription>
          </Alert>
        )}

        {/* No Plans Available Warning */}
        {plans.length === 0 && !error && (
          <Alert className="mb-6">
            <AlertDescription>
              No subscription plans are currently available. Please contact support or try again later.
            </AlertDescription>
          </Alert>
        )}

        {/* Signup Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Organization Name */}
          <div className="space-y-2">
            <Label htmlFor="tenant_name" className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-gray-500" />
              Organization Name
            </Label>
            <Input
              id="tenant_name"
              placeholder="acme-pharma"
              {...register('tenant_name')}
              className={errors.tenant_name ? 'border-red-500' : ''}
            />
            {errors.tenant_name && (
              <p className="text-sm text-red-500">{errors.tenant_name.message}</p>
            )}
            <p className="text-xs text-gray-500">
              This will be used in your workspace URL (e.g., acme-pharma.pearl.app)
            </p>
          </div>

          {/* Display Name (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="display_name">
              Display Name <span className="text-gray-400">(optional)</span>
            </Label>
            <Input
              id="display_name"
              placeholder="ACME Pharma Inc."
              {...register('display_name')}
            />
            <p className="text-xs text-gray-500">
              How your organization name will appear in the app
            </p>
          </div>

          {/* Email */}
          <div className="space-y-2">
            <Label htmlFor="email" className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-gray-500" />
              Admin Email
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="admin@acme-pharma.com"
              {...register('email')}
              className={errors.email ? 'border-red-500' : ''}
            />
            {errors.email && (
              <p className="text-sm text-red-500">{errors.email.message}</p>
            )}
            <p className="text-xs text-gray-500">
              We'll send your login credentials here
            </p>
          </div>

          {/* Plan Selection */}
          <div className="space-y-2">
            <Label htmlFor="plan_id" className="flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-gray-500" />
              Select Plan
            </Label>
            <Select
              value={selectedPlanId}
              onValueChange={(value) => setValue('plan_id', value)}
            >
              <SelectTrigger className={errors.plan_id ? 'border-red-500' : ''}>
                <SelectValue placeholder="Choose a plan" />
              </SelectTrigger>
              <SelectContent>
                {plans
                  .filter(p => p.price_monthly > 0) // Exclude enterprise (contact sales)
                  .map((plan) => (
                    <SelectItem key={plan.id} value={plan.id.toString()}>
                      {plan.display_name} - {formatPrice(plan.price_monthly)}/mo
                      {plan.is_popular && ' ⭐'}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            {errors.plan_id && (
              <p className="text-sm text-red-500">{errors.plan_id.message}</p>
            )}
          </div>

          {/* Selected Plan Summary */}
          {selectedPlan && (
            <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-100">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium text-gray-900">{selectedPlan.display_name}</span>
                <span className="font-bold text-indigo-600">
                  {formatPrice(selectedPlan.price_monthly)}/month
                </span>
              </div>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• {selectedPlan.max_users === -1 ? 'Unlimited' : selectedPlan.max_users} users</li>
                <li>• {selectedPlan.max_studies === -1 ? 'Unlimited' : selectedPlan.max_studies} studies</li>
                <li>• {trialDays}-day free trial</li>
              </ul>
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            size="lg"
            className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
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
          <p className="text-xs text-center text-gray-500">
            By signing up, you agree to our{' '}
            <Link to="/terms" className="text-indigo-600 hover:underline">Terms of Service</Link>
            {' '}and{' '}
            <Link to="/privacy" className="text-indigo-600 hover:underline">Privacy Policy</Link>
          </p>
        </form>

        {/* Already have account */}
        <div className="mt-8 text-center">
          <p className="text-gray-600">
            Already have an account?{' '}
            <Link to="/app/login" className="text-indigo-600 font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
