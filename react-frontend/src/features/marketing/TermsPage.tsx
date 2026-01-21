/**
 * Terms of Service Page
 *
 * Legal terms covering Stripe payments, Railway hosting,
 * and no-refund cancellation policy
 */

import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export function TermsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-9 h-9 bg-teal-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">P</span>
              </div>
              <span className="font-semibold text-xl text-slate-900 tracking-tight">PEARL</span>
            </Link>
            <Link
              to="/"
              className="text-slate-600 hover:text-slate-900 font-medium flex items-center gap-2 text-sm"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Home
            </Link>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-4 py-16">
        <h1 className="text-4xl font-bold text-slate-900 mb-8">Terms of Service</h1>

        <div className="prose prose-slate max-w-none">
          <p className="text-slate-600 mb-6">
            <em>Last updated: January 21, 2026</em>
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">1. Acceptance of Terms</h2>
          <p className="text-slate-600 mb-4">
            By accessing or using PEARL ("the Service"), you agree to be bound by these Terms of Service.
            If you do not agree to these terms, do not use the Service. These terms apply to all users,
            including organization administrators and team members.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">2. Description of Service</h2>
          <p className="text-slate-600 mb-4">
            PEARL is a clinical research data management platform that helps biostatistics teams manage
            TFL (Tables, Figures, Listings) packages, track production status, and collaborate on reporting
            efforts. The Service is provided as a subscription-based software-as-a-service (SaaS) platform.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">3. Account Registration</h2>
          <p className="text-slate-600 mb-4">
            To use the Service, you must create an account with accurate and complete information. You are
            responsible for:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li>Maintaining the confidentiality of your account credentials</li>
            <li>All activities that occur under your account</li>
            <li>Notifying us immediately of any unauthorized access</li>
            <li>Ensuring that team members comply with these terms</li>
          </ul>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">4. Subscription Plans and Billing</h2>
          <p className="text-slate-600 mb-4">
            The Service offers various subscription plans with different features and user limits.
            By selecting a paid plan, you agree to pay the applicable fees.
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li><strong>Billing Cycle:</strong> Subscriptions are billed in advance on a monthly or annual basis, depending on your selected plan.</li>
            <li><strong>Payment Processing:</strong> All payments are processed securely through Stripe, Inc. By using our Service, you also agree to <a href="https://stripe.com/legal" target="_blank" rel="noopener noreferrer" className="text-teal-600 hover:underline">Stripe's Terms of Service</a>.</li>
            <li><strong>Automatic Renewal:</strong> Your subscription will automatically renew at the end of each billing period unless cancelled.</li>
            <li><strong>Price Changes:</strong> We may change subscription prices with 30 days' notice. Price changes take effect at your next billing cycle.</li>
          </ul>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">5. Cancellation and Refund Policy</h2>
          <div className="bg-slate-100 border border-slate-200 rounded-lg p-4 mb-4">
            <p className="text-slate-700 font-medium mb-2">Important: No Refunds</p>
            <p className="text-slate-600">
              <strong>All subscription fees are non-refundable.</strong> When you cancel your subscription:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mt-2 space-y-1">
              <li>Your subscription will remain active until the end of your current billing period</li>
              <li>You will retain full access to the Service until that date</li>
              <li>Your subscription will not renew for the next billing period</li>
              <li>No partial refunds are provided for unused time</li>
            </ul>
          </div>
          <p className="text-slate-600 mb-4">
            You may cancel your subscription at any time through your account settings or by contacting
            support. Cancellation takes effect at the end of your current billing period.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">6. Free Trial</h2>
          <p className="text-slate-600 mb-4">
            We may offer a free trial period. At the end of the trial, you will be automatically enrolled
            in your selected paid plan unless you cancel before the trial ends. No payment will be charged
            during the trial period.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">7. Acceptable Use</h2>
          <p className="text-slate-600 mb-4">
            You agree not to:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li>Use the Service for any unlawful purpose</li>
            <li>Attempt to gain unauthorized access to any part of the Service</li>
            <li>Interfere with or disrupt the Service or servers</li>
            <li>Upload malicious code or content</li>
            <li>Share account credentials with unauthorized parties</li>
            <li>Exceed your plan's user or storage limits</li>
            <li>Resell or redistribute the Service without authorization</li>
          </ul>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">8. Data Ownership</h2>
          <p className="text-slate-600 mb-4">
            You retain all rights to the data you upload to the Service ("Your Data"). We do not claim
            ownership of Your Data. By using the Service, you grant us a limited license to host, store,
            and process Your Data solely to provide the Service to you.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">9. Service Availability</h2>
          <p className="text-slate-600 mb-4">
            We strive to maintain high availability but do not guarantee uninterrupted access. The Service
            is hosted on Railway infrastructure. We may perform scheduled maintenance with advance notice
            when possible. We are not liable for any downtime or service interruptions.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">10. Limitation of Liability</h2>
          <p className="text-slate-600 mb-4">
            TO THE MAXIMUM EXTENT PERMITTED BY LAW, PEARL AND ITS AFFILIATES SHALL NOT BE LIABLE FOR ANY
            INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED
            TO LOSS OF PROFITS, DATA, OR BUSINESS OPPORTUNITIES, ARISING FROM YOUR USE OF THE SERVICE.
          </p>
          <p className="text-slate-600 mb-4">
            OUR TOTAL LIABILITY FOR ANY CLAIMS ARISING FROM THESE TERMS OR YOUR USE OF THE SERVICE SHALL
            NOT EXCEED THE AMOUNT YOU PAID US IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">11. Disclaimer of Warranties</h2>
          <p className="text-slate-600 mb-4">
            THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
            PURPOSE, AND NON-INFRINGEMENT.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">12. Indemnification</h2>
          <p className="text-slate-600 mb-4">
            You agree to indemnify and hold harmless PEARL and its officers, directors, employees, and
            agents from any claims, damages, or expenses arising from your use of the Service, your
            violation of these Terms, or your violation of any rights of a third party.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">13. Termination</h2>
          <p className="text-slate-600 mb-4">
            We may suspend or terminate your access to the Service at any time for violation of these
            Terms or for any other reason at our discretion. Upon termination:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li>Your right to use the Service immediately ceases</li>
            <li>You may request export of Your Data within 30 days</li>
            <li>We may delete Your Data after a reasonable retention period</li>
          </ul>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">14. Changes to Terms</h2>
          <p className="text-slate-600 mb-4">
            We may update these Terms from time to time. We will notify you of material changes via email
            or through the Service. Your continued use of the Service after such changes constitutes
            acceptance of the updated Terms.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">15. Governing Law</h2>
          <p className="text-slate-600 mb-4">
            These Terms shall be governed by and construed in accordance with the laws of the jurisdiction
            in which PEARL operates, without regard to conflict of law principles.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">16. Contact</h2>
          <p className="text-slate-600 mb-4">
            For questions about these Terms of Service, please contact us at{' '}
            <a href="mailto:legal@pearl.app" className="text-teal-600 hover:underline">
              legal@pearl.app
            </a>
          </p>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-8 px-4">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">P</span>
            </div>
            <span className="font-semibold text-white">PEARL</span>
          </div>
          <div className="flex gap-6 text-sm">
            <Link to="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
            <Link to="/terms" className="hover:text-white transition-colors">Terms of Service</Link>
          </div>
          <div className="text-sm">
            © {new Date().getFullYear()} PEARL. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
