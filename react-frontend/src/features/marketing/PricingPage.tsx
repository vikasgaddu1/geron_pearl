/**
 * Pricing Page
 * 
 * Displays subscription plans with:
 * - Plan tiers with features
 * - Feature comparison table
 * - FAQ section
 */

import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Check, X, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getPlans, Plan, formatPrice } from '@/api/endpoints/billing';

const featureComparison = [
  { name: 'Users', starter: '5', professional: '25', enterprise: 'Unlimited' },
  { name: 'Studies', starter: '10', professional: 'Unlimited', enterprise: 'Unlimited' },
  { name: 'Storage', starter: '1 GB', professional: '10 GB', enterprise: 'Unlimited' },
  { name: 'Email Support', starter: true, professional: true, enterprise: true },
  { name: 'API Access', starter: false, professional: true, enterprise: true },
  { name: 'Priority Support', starter: false, professional: true, enterprise: true },
  { name: 'Custom Branding', starter: false, professional: true, enterprise: true },
  { name: 'SSO / SAML', starter: false, professional: false, enterprise: true },
  { name: 'Dedicated Support', starter: false, professional: false, enterprise: true },
  { name: 'Custom Integrations', starter: false, professional: false, enterprise: true },
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
        // Defensive: handle cases where plans might be undefined or not an array
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
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">P</span>
              </div>
              <span className="font-bold text-xl text-gray-900">PEARL</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link to="/app/login" className="text-gray-600 hover:text-gray-900 font-medium">
                Login
              </Link>
              <Link to="/signup">
                <Button className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700">
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
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Your signup was canceled. Feel free to try again when you're ready.
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Header */}
      <section className="pt-20 pb-12 px-4 sm:px-6 lg:px-8 text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Simple, transparent pricing
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-8">
          Choose the plan that fits your team. All plans include a 30-day free trial.
        </p>

        {/* Billing Period Toggle */}
        <div className="inline-flex items-center bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setBillingPeriod('monthly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              billingPeriod === 'monthly'
                ? 'bg-white shadow text-gray-900'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingPeriod('yearly')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              billingPeriod === 'yearly'
                ? 'bg-white shadow text-gray-900'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Yearly
            <Badge variant="secondary" className="ml-2 bg-green-100 text-green-700">
              Save 17%
            </Badge>
          </button>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
          ) : error ? (
            <div className="text-center py-12 text-red-600">{error}</div>
          ) : plans.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No pricing plans are currently available.</p>
              <p className="text-sm text-gray-500">Please contact us for custom pricing options.</p>
              <a href="mailto:sales@pearl.app" className="inline-block mt-4">
                <Button variant="outline">Contact Sales</Button>
              </a>
            </div>
          ) : (
            <div className="grid md:grid-cols-3 gap-8">
              {plans.map((plan) => (
                <div
                  key={plan.id}
                  className={`relative bg-white rounded-2xl border-2 p-8 ${
                    plan.is_popular
                      ? 'border-indigo-500 shadow-xl'
                      : 'border-gray-200'
                  }`}
                >
                  {plan.is_popular && (
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                      <Badge className="bg-indigo-500 text-white px-4 py-1">
                        Most Popular
                      </Badge>
                    </div>
                  )}
                  <div className="text-center mb-8">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">
                      {plan.display_name}
                    </h3>
                    <p className="text-gray-600 text-sm h-12">
                      {plan.description}
                    </p>
                    <div className="mt-6">
                      <span className="text-4xl font-bold text-gray-900">
                        {getPrice(plan)}
                      </span>
                      {plan.price_monthly > 0 && (
                        <span className="text-gray-600">/month</span>
                      )}
                    </div>
                    {billingPeriod === 'yearly' && plan.price_yearly && (
                      <p className="text-sm text-gray-500 mt-1">
                        billed annually
                      </p>
                    )}
                  </div>

                  <ul className="space-y-3 mb-8">
                    <li className="flex items-center gap-3 text-gray-600">
                      <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                      <span>
                        {plan.max_users === -1 ? 'Unlimited' : plan.max_users} users
                      </span>
                    </li>
                    <li className="flex items-center gap-3 text-gray-600">
                      <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                      <span>
                        {plan.max_studies === -1 ? 'Unlimited' : plan.max_studies} studies
                      </span>
                    </li>
                    <li className="flex items-center gap-3 text-gray-600">
                      <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                      <span>
                        {plan.max_storage_mb === -1
                          ? 'Unlimited storage'
                          : `${plan.max_storage_mb >= 1024 
                              ? `${plan.max_storage_mb / 1024} GB` 
                              : `${plan.max_storage_mb} MB`} storage`}
                      </span>
                    </li>
                    {plan.features?.api_access && (
                      <li className="flex items-center gap-3 text-gray-600">
                        <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                        <span>API access</span>
                      </li>
                    )}
                    {plan.features?.priority_support && (
                      <li className="flex items-center gap-3 text-gray-600">
                        <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                        <span>Priority support</span>
                      </li>
                    )}
                    {plan.features?.sso && (
                      <li className="flex items-center gap-3 text-gray-600">
                        <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                        <span>SSO / SAML</span>
                      </li>
                    )}
                  </ul>

                  {plan.price_monthly === 0 ? (
                    <a href="mailto:sales@pearl.app?subject=Enterprise%20Plan%20Inquiry" className="block">
                      <Button variant="outline" size="lg" className="w-full">
                        Contact Sales
                      </Button>
                    </a>
                  ) : (
                    <Link to={`/signup?plan=${plan.id}`} className="block">
                      <Button
                        className={`w-full ${
                          plan.is_popular
                            ? 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700'
                            : ''
                        }`}
                        variant={plan.is_popular ? 'default' : 'outline'}
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
      <section className="py-24 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Compare plans
          </h2>
          <div className="bg-white rounded-xl border overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left p-4 font-semibold text-gray-900">Feature</th>
                  <th className="text-center p-4 font-semibold text-gray-900">Starter</th>
                  <th className="text-center p-4 font-semibold text-gray-900 bg-indigo-50">
                    Professional
                  </th>
                  <th className="text-center p-4 font-semibold text-gray-900">Enterprise</th>
                </tr>
              </thead>
              <tbody>
                {featureComparison.map((feature, index) => (
                  <tr key={feature.name} className={index % 2 === 0 ? 'bg-gray-50/50' : ''}>
                    <td className="p-4 text-gray-600">{feature.name}</td>
                    <td className="p-4 text-center">
                      {typeof feature.starter === 'boolean' ? (
                        feature.starter ? (
                          <Check className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <X className="h-5 w-5 text-gray-300 mx-auto" />
                        )
                      ) : (
                        <span className="text-gray-900">{feature.starter}</span>
                      )}
                    </td>
                    <td className="p-4 text-center bg-indigo-50/50">
                      {typeof feature.professional === 'boolean' ? (
                        feature.professional ? (
                          <Check className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <X className="h-5 w-5 text-gray-300 mx-auto" />
                        )
                      ) : (
                        <span className="text-gray-900 font-medium">{feature.professional}</span>
                      )}
                    </td>
                    <td className="p-4 text-center">
                      {typeof feature.enterprise === 'boolean' ? (
                        feature.enterprise ? (
                          <Check className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <X className="h-5 w-5 text-gray-300 mx-auto" />
                        )
                      ) : (
                        <span className="text-gray-900">{feature.enterprise}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Frequently asked questions
          </h2>
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <AccordionItem 
                key={index} 
                value={`item-${index}`}
                className="bg-white rounded-lg border px-6"
              >
                <AccordionTrigger className="text-left font-medium text-gray-900 hover:no-underline">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-gray-600">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">P</span>
            </div>
            <span className="font-bold text-xl text-white">PEARL</span>
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
