/**
 * Pricing Page
 *
 * Clean clinical design with:
 * - Plan tiers with features
 * - Feature comparison table
 * - FAQ section
 */

import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Check, X, Loader2, AlertCircle, Calculator, Users, FolderOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getPlans, Plan, formatPrice } from '@/api/endpoints/billing';

const featureComparison = [
  // Limits
  { name: 'Team Members', starter: '12', professional: '100', enterprise: 'Custom' },
  { name: 'Studies', starter: '3', professional: '15', enterprise: 'Custom' },
  { name: 'Tracker Items', starter: '1,000', professional: '10,000', enterprise: 'Unlimited' },
  // Core Features
  { name: 'TFL Package Management', starter: true, professional: true, enterprise: true },
  { name: 'Real-time Collaboration', starter: true, professional: true, enterprise: true },
  { name: 'Audit Trail', starter: true, professional: true, enterprise: true },
  { name: 'Role-based Access Control', starter: true, professional: true, enterprise: true },
  // Support
  { name: 'Email Support', starter: true, professional: true, enterprise: true },
  { name: 'Priority Support', starter: false, professional: true, enterprise: true },
  { name: 'Dedicated Account Manager', starter: false, professional: false, enterprise: true },
  // Advanced Features
  { name: 'API Access', starter: false, professional: true, enterprise: true },
  { name: 'Custom Branding', starter: false, professional: true, enterprise: true },
  { name: 'SSO / SAML', starter: false, professional: false, enterprise: true },
  { name: 'Custom Integrations', starter: false, professional: false, enterprise: true },
  { name: 'SLA Guarantee', starter: false, professional: false, enterprise: true },
];

const faqs = [
  {
    question: 'Can I change plans later?',
    answer: 'Yes, you can upgrade or downgrade your plan at any time. When upgrading, you\'ll be charged a prorated amount for the remainder of your billing period. When downgrading, the new rate takes effect at the start of your next billing period.',
  },
  {
    question: 'What happens when my trial ends?',
    answer: 'At the end of your 30-day trial, you\'ll be asked to add a payment method to continue using PEARL. If you don\'t add a payment method, your access will be restricted until you subscribe.',
  },
  {
    question: 'Is there a setup fee?',
    answer: 'No, there are no setup fees or hidden costs. You only pay your subscription fee.',
  },
  {
    question: 'Can I cancel anytime?',
    answer: 'Yes, you can cancel your subscription at any time. Your access will continue until the end of your current billing period.',
  },
  {
    question: 'Do you offer discounts for annual billing?',
    answer: 'Yes! Annual billing includes 2 months free compared to monthly billing. Contact us for enterprise pricing.',
  },
  {
    question: 'Is my data secure?',
    answer: 'Absolutely. We use industry-standard encryption, run on SOC 2 Type II certified infrastructure, and follow HIPAA-compliant practices. Your data is isolated using Row-Level Security and is never shared between tenants.',
  },
  {
    question: 'Can I export my data?',
    answer: 'Yes, you can export all your data at any time in standard formats. We believe your data belongs to you.',
  },
];

// Enterprise pricing constants
const ENTERPRISE_BASE_FEE = 500; // $500/month base
const ENTERPRISE_PER_USER = 5; // $5 per user above 100
const ENTERPRISE_PER_STUDY = 50; // $50 per study above 15
const ENTERPRISE_INCLUDED_USERS = 100;
const ENTERPRISE_INCLUDED_STUDIES = 15;

function EnterpriseCalculator() {
  const [users, setUsers] = useState(150);
  const [studies, setStudies] = useState(25);

  // Calculate monthly price
  const extraUsers = Math.max(0, users - ENTERPRISE_INCLUDED_USERS);
  const extraStudies = Math.max(0, studies - ENTERPRISE_INCLUDED_STUDIES);
  const monthlyPrice = ENTERPRISE_BASE_FEE + (extraUsers * ENTERPRISE_PER_USER) + (extraStudies * ENTERPRISE_PER_STUDY);
  const yearlyPrice = monthlyPrice * 10; // 2 months free (17% discount)
  const monthlySavings = (monthlyPrice * 12) - yearlyPrice;

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-slate-200 text-slate-700 px-3 py-1.5 rounded-full text-sm font-medium mb-4">
            <Calculator className="h-4 w-4" />
            Enterprise Pricing Estimator
          </div>
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            Estimate your enterprise cost
          </h2>
          <p className="text-slate-600">
            Get an instant estimate for your organization. Final pricing confirmed during sales consultation.
          </p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-8">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Inputs */}
            <div className="space-y-6">
              {/* Users Input */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2 text-sm font-medium">
                  <Users className="h-4 w-4 text-slate-400" />
                  Team Members
                </Label>
                <Input
                  type="number"
                  value={users}
                  onChange={(e) => setUsers(Math.max(100, parseInt(e.target.value) || 100))}
                  min={100}
                  className="h-11 text-lg"
                />
                <p className="text-xs text-slate-500">
                  First 100 users included, then ${ENTERPRISE_PER_USER}/user
                </p>
              </div>

              {/* Studies Input */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2 text-sm font-medium">
                  <FolderOpen className="h-4 w-4 text-slate-400" />
                  Active Studies
                </Label>
                <Input
                  type="number"
                  value={studies}
                  onChange={(e) => setStudies(Math.max(15, parseInt(e.target.value) || 15))}
                  min={15}
                  className="h-11 text-lg"
                />
                <p className="text-xs text-slate-500">
                  First 15 studies included, then ${ENTERPRISE_PER_STUDY}/study
                </p>
              </div>

              {/* Quick presets */}
              <div className="pt-4 border-t border-slate-100">
                <p className="text-xs text-slate-500 mb-2">Quick presets:</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    { users: 150, studies: 20, label: 'Small' },
                    { users: 250, studies: 40, label: 'Medium' },
                    { users: 500, studies: 75, label: 'Large' },
                  ].map((preset) => (
                    <button
                      key={preset.label}
                      type="button"
                      onClick={() => { setUsers(preset.users); setStudies(preset.studies); }}
                      className="px-3 py-1.5 text-xs font-medium rounded-md border border-slate-200 hover:bg-slate-50 hover:border-slate-300 transition-colors"
                    >
                      {preset.label} ({preset.users} users, {preset.studies} studies)
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Price Display */}
            <div className="bg-slate-50 rounded-lg p-6 border border-slate-200">
              <div className="text-center">
                <p className="text-sm text-slate-500 mb-1">Estimated Annual Price</p>
                <div className="text-4xl font-bold text-slate-900 mb-1">
                  ${yearlyPrice.toLocaleString()}
                  <span className="text-lg font-normal text-slate-500">/year</span>
                </div>
                <p className="text-sm text-teal-600 font-medium mb-6">
                  Save ${monthlySavings.toLocaleString()} vs monthly
                </p>

                {/* Breakdown */}
                <div className="text-left space-y-2 pt-4 border-t border-slate-200">
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
                    Monthly Breakdown
                  </p>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Base fee</span>
                    <span className="text-slate-900">${ENTERPRISE_BASE_FEE}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">{extraUsers} extra users × ${ENTERPRISE_PER_USER}</span>
                    <span className="text-slate-900">${extraUsers * ENTERPRISE_PER_USER}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">{extraStudies} extra studies × ${ENTERPRISE_PER_STUDY}</span>
                    <span className="text-slate-900">${extraStudies * ENTERPRISE_PER_STUDY}</span>
                  </div>
                  <div className="flex justify-between text-sm font-medium pt-2 border-t border-slate-200">
                    <span className="text-slate-900">Monthly equivalent</span>
                    <span className="text-slate-900">${monthlyPrice.toLocaleString()}/mo</span>
                  </div>
                </div>

                <a
                  href={`mailto:sales@pearl.app?subject=Enterprise%20Inquiry&body=Hi,%0A%0AI'm%20interested%20in%20PEARL%20Enterprise%20for%20approximately%20${users}%20users%20and%20${studies}%20studies.%0A%0AEstimated%20annual%20cost:%20$${yearlyPrice.toLocaleString()}%0A%0APlease%20contact%20me%20to%20discuss.`}
                  className="block mt-6"
                >
                  <Button className="w-full bg-slate-900 hover:bg-slate-800 text-white">
                    Contact Sales
                  </Button>
                </a>
                <p className="text-xs text-slate-500 mt-3">
                  Enterprise plans are billed annually
                </p>
              </div>
            </div>
          </div>

          {/* Included Features */}
          <div className="mt-8 pt-6 border-t border-slate-200">
            <p className="text-sm font-medium text-slate-900 mb-3">All Enterprise plans include:</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {['SSO / SAML', 'Dedicated Support', 'Custom Integrations', 'SLA Guarantee'].map((feature) => (
                <div key={feature} className="flex items-center gap-2 text-sm text-slate-600">
                  <Check className="h-4 w-4 text-teal-600 flex-shrink-0" />
                  {feature}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function PricingPage() {
  const [searchParams] = useSearchParams();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');

  const canceled = searchParams.get('canceled') === 'true';

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const response = await getPlans();
        setPlans(response?.plans ?? []);
      } catch (err) {
        console.error('Failed to fetch plans:', err);
        setError('Failed to load pricing plans. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, []);

  const getPrice = (plan: Plan) => {
    if (plan.price_monthly === 0) return 'Custom';
    if (billingPeriod === 'yearly' && plan.price_yearly) {
      return `$${(plan.price_yearly / 100 / 12).toFixed(0)}`;
    }
    return formatPrice(plan.price_monthly);
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-slate-200 bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-9 h-9 bg-teal-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">P</span>
              </div>
              <span className="font-semibold text-xl text-slate-900 tracking-tight">PEARL</span>
            </Link>
            <div className="flex items-center gap-6">
              <Link to="/app/login" className="text-slate-600 hover:text-slate-900 font-medium text-sm">
                Sign in
              </Link>
              <Link to="/signup">
                <Button className="bg-teal-600 hover:bg-teal-700 text-white font-medium">
                  Start Free Trial
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Canceled Alert */}
      {canceled && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
          <Alert className="border-slate-200">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Your signup was canceled. Feel free to try again when you're ready.
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Header */}
      <section className="pt-16 pb-12 px-4 sm:px-6 lg:px-8 text-center bg-slate-50">
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          Simple, transparent pricing
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
          Choose the plan that fits your team. All plans include a 30-day free trial.
        </p>

        {/* Billing Period Toggle */}
        <div className="inline-flex items-center bg-slate-200 rounded-lg p-1">
          <button
            onClick={() => setBillingPeriod('monthly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              billingPeriod === 'monthly'
                ? 'bg-white shadow text-slate-900'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingPeriod('yearly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
              billingPeriod === 'yearly'
                ? 'bg-white shadow text-slate-900'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Yearly
            <Badge variant="secondary" className="bg-teal-100 text-teal-700 border-0">
              Save 17%
            </Badge>
          </button>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-600">{error}</div>
          ) : plans.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-slate-600 mb-4">No pricing plans are currently available.</p>
              <p className="text-sm text-slate-500">Please contact us for custom pricing options.</p>
              <a href="mailto:sales@pearl.app" className="inline-block mt-4">
                <Button variant="outline" className="border-slate-300">Contact Sales</Button>
              </a>
            </div>
          ) : (
            <div className="grid md:grid-cols-3 gap-6">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className={`relative bg-white rounded-xl border-2 p-8 ${
                    plan.is_popular
                      ? 'border-teal-500 shadow-lg'
                      : 'border-slate-200'
                  }`}
                >
                  {plan.is_popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <Badge className="bg-teal-600 text-white px-3 py-1 text-xs font-medium">
                        Most Popular
                      </Badge>
                    </div>
                  )}
                  <div className="text-center mb-8">
                    <h3 className="text-xl font-semibold text-slate-900 mb-2">
                      {plan.display_name}
                    </h3>
                    <p className="text-slate-600 text-sm h-12">
                      {plan.description}
                    </p>
                    <div className="mt-6">
                      <span className="text-4xl font-bold text-slate-900">
                        {getPrice(plan)}
                      </span>
                      {plan.price_monthly > 0 && (
                        <span className="text-slate-500">/month</span>
                      )}
                    </div>
                    {billingPeriod === 'yearly' && plan.price_yearly > 0 && (
                      <p className="text-sm text-slate-500 mt-1">
                        billed annually
                      </p>
                    )}
                  </div>

                  <ul className="space-y-3 mb-8">
                    <li className="flex items-center gap-3 text-slate-600 text-sm">
                      <Check className="h-4 w-4 text-teal-600 flex-shrink-0" />
                      <span>
                        {plan.max_users === -1 ? 'Unlimited' : plan.max_users} users
                      </span>
                    </li>
                    <li className="flex items-center gap-3 text-slate-600 text-sm">
                      <Check className="h-4 w-4 text-teal-600 flex-shrink-0" />
                      <span>
                        {plan.max_studies === -1 ? 'Unlimited' : plan.max_studies} studies
                      </span>
                    </li>
                    <li className="flex items-center gap-3 text-slate-600 text-sm">
                      <Check className="h-4 w-4 text-teal-600 flex-shrink-0" />
                      <span>
                        {plan.max_tracker_items === -1
                          ? 'Unlimited tracker items'
                          : `${plan.max_tracker_items.toLocaleString()} tracker items`}
                      </span>
                    </li>
                    {plan.features?.api_access && (
                      <li className="flex items-center gap-3 text-slate-600 text-sm">
                        <Check className="h-4 w-4 text-teal-600 flex-shrink-0" />
                        <span>API access</span>
                      </li>
                    )}
                    {plan.features?.priority_support && (
                      <li className="flex items-center gap-3 text-slate-600 text-sm">
                        <Check className="h-4 w-4 text-teal-600 flex-shrink-0" />
                        <span>Priority support</span>
                      </li>
                    )}
                    {plan.features?.sso && (
                      <li className="flex items-center gap-3 text-slate-600 text-sm">
                        <Check className="h-4 w-4 text-teal-600 flex-shrink-0" />
                        <span>SSO / SAML</span>
                      </li>
                    )}
                  </ul>

                  {plan.price_monthly === 0 ? (
                    <a href="mailto:sales@pearl.app?subject=Enterprise%20Plan%20Inquiry" className="block">
                      <Button variant="outline" size="lg" className="w-full border-slate-300 text-slate-700 hover:bg-slate-50">
                        Contact Sales
                      </Button>
                    </a>
                  ) : (
                    <Link to={`/signup?plan=${plan.id}&billing=${billingPeriod}`} className="block">
                      <Button
                        className={`w-full ${
                          plan.is_popular
                            ? 'bg-teal-600 hover:bg-teal-700 text-white'
                            : 'bg-slate-900 hover:bg-slate-800 text-white'
                        }`}
                        size="lg"
                      >
                        Start Free Trial
                      </Button>
                    </Link>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Feature Comparison */}
      <section className="py-20 bg-white px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-900 text-center mb-12">
            Compare plans
          </h2>
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="text-left p-4 font-semibold text-slate-900 text-sm">Feature</th>
                  <th className="text-center p-4 font-semibold text-slate-900 text-sm bg-teal-50">
                    Starter
                  </th>
                  <th className="text-center p-4 font-semibold text-slate-900 text-sm">
                    Professional
                  </th>
                  <th className="text-center p-4 font-semibold text-slate-900 text-sm">Enterprise</th>
                </tr>
              </thead>
              <tbody>
                {featureComparison.map((feature, index) => (
                  <tr key={feature.name} className={index % 2 === 0 ? '' : 'bg-slate-50/50'}>
                    <td className="p-4 text-slate-600 text-sm">{feature.name}</td>
                    <td className="p-4 text-center bg-teal-50/50">
                      {typeof feature.starter === 'boolean' ? (
                        feature.starter ? (
                          <Check className="h-4 w-4 text-teal-600 mx-auto" />
                        ) : (
                          <X className="h-4 w-4 text-slate-300 mx-auto" />
                        )
                      ) : (
                        <span className="text-slate-900 font-medium text-sm">{feature.starter}</span>
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {typeof feature.professional === 'boolean' ? (
                        feature.professional ? (
                          <Check className="h-4 w-4 text-teal-600 mx-auto" />
                        ) : (
                          <X className="h-4 w-4 text-slate-300 mx-auto" />
                        )
                      ) : (
                        <span className="text-slate-900 text-sm">{feature.professional}</span>
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {typeof feature.enterprise === 'boolean' ? (
                        feature.enterprise ? (
                          <Check className="h-4 w-4 text-teal-600 mx-auto" />
                        ) : (
                          <X className="h-4 w-4 text-slate-300 mx-auto" />
                        )
                      ) : (
                        <span className="text-slate-900 text-sm">{feature.enterprise}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Enterprise Calculator */}
      <EnterpriseCalculator />

      {/* FAQ Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-slate-900 text-center mb-12">
            Frequently asked questions
          </h2>
          <Accordion type="single" collapsible className="space-y-3">
            {faqs.map((faq, index) => (
              <AccordionItem
                key={index}
                value={`item-${index}`}
                className="bg-white rounded-lg border border-slate-200 px-6"
              >
                <AccordionTrigger className="text-left font-medium text-slate-900 hover:no-underline text-sm">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-slate-600 text-sm">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-9 h-9 bg-teal-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">P</span>
            </div>
            <span className="font-semibold text-xl text-white">PEARL</span>
          </div>
          <p className="text-sm mb-4">
            Package, Effort and Analysis Reporting Library
          </p>
          <div className="text-sm">
            © {new Date().getFullYear()} PEARL. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
