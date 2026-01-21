/**
 * Privacy Policy Page
 *
 * Privacy policy covering data collection, Stripe payment processing,
 * Railway hosting, and user rights
 */

import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export function PrivacyPage() {
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
        <h1 className="text-4xl font-bold text-slate-900 mb-8">Privacy Policy</h1>

        <div className="prose prose-slate max-w-none">
          <p className="text-slate-600 mb-6">
            <em>Last updated: January 21, 2026</em>
          </p>

          <p className="text-slate-600 mb-6">
            This Privacy Policy describes how PEARL ("we", "us", or "our") collects, uses, and protects
            your information when you use our clinical research data management platform ("the Service").
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">1. Information We Collect</h2>

          <h3 className="text-lg font-semibold text-slate-800 mt-6 mb-3">Account Information</h3>
          <p className="text-slate-600 mb-4">
            When you create an account, we collect:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li>Name and email address</li>
            <li>Organization name</li>
            <li>Password (stored securely using industry-standard hashing)</li>
            <li>Role and permissions within your organization</li>
          </ul>

          <h3 className="text-lg font-semibold text-slate-800 mt-6 mb-3">Usage Data</h3>
          <p className="text-slate-600 mb-4">
            We automatically collect certain information when you use the Service:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li>IP address and browser type</li>
            <li>Pages visited and features used</li>
            <li>Date and time of access</li>
            <li>Error logs and performance data</li>
          </ul>

          <h3 className="text-lg font-semibold text-slate-800 mt-6 mb-3">Your Data</h3>
          <p className="text-slate-600 mb-4">
            You upload and create data within the Service, including:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li>Study information and configurations</li>
            <li>TFL package definitions and metadata</li>
            <li>Tracker assignments and status updates</li>
            <li>Comments and collaboration content</li>
          </ul>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">2. How We Use Your Information</h2>
          <p className="text-slate-600 mb-4">
            We use the information we collect to:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li>Provide, maintain, and improve the Service</li>
            <li>Process transactions and send related information</li>
            <li>Send technical notices, updates, and support messages</li>
            <li>Respond to your comments, questions, and requests</li>
            <li>Monitor and analyze usage trends</li>
            <li>Detect, prevent, and address technical issues or fraud</li>
            <li>Comply with legal obligations</li>
          </ul>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">3. Third-Party Service Providers</h2>
          <p className="text-slate-600 mb-4">
            We use trusted third-party services to operate our platform:
          </p>

          <div className="bg-slate-100 border border-slate-200 rounded-lg p-4 mb-4">
            <h4 className="font-semibold text-slate-800 mb-2">Stripe (Payment Processing)</h4>
            <p className="text-slate-600 text-sm mb-2">
              We use Stripe to process subscription payments. When you provide payment information,
              it is transmitted directly to Stripe and is not stored on our servers. Stripe may collect:
            </p>
            <ul className="list-disc pl-6 text-slate-600 text-sm space-y-1">
              <li>Credit/debit card details</li>
              <li>Billing address</li>
              <li>Transaction history</li>
            </ul>
            <p className="text-slate-600 text-sm mt-2">
              Stripe's handling of your data is governed by their{' '}
              <a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer" className="text-teal-600 hover:underline">
                Privacy Policy
              </a>.
            </p>
          </div>

          <div className="bg-slate-100 border border-slate-200 rounded-lg p-4 mb-4">
            <h4 className="font-semibold text-slate-800 mb-2">Railway (Cloud Hosting)</h4>
            <p className="text-slate-600 text-sm mb-2">
              Our Service is hosted on Railway's cloud infrastructure. Railway provides secure,
              scalable hosting and may process:
            </p>
            <ul className="list-disc pl-6 text-slate-600 text-sm space-y-1">
              <li>Server logs and access data</li>
              <li>Application data stored in databases</li>
              <li>Files and backups</li>
            </ul>
            <p className="text-slate-600 text-sm mt-2">
              Railway's data practices are described in their{' '}
              <a href="https://railway.app/legal/privacy" target="_blank" rel="noopener noreferrer" className="text-teal-600 hover:underline">
                Privacy Policy
              </a>.
            </p>
          </div>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">4. Data Security</h2>
          <p className="text-slate-600 mb-4">
            We implement appropriate technical and organizational measures to protect your data:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li><strong>Encryption:</strong> Data is encrypted in transit (TLS/HTTPS) and at rest</li>
            <li><strong>Access Control:</strong> Role-based permissions limit data access to authorized users</li>
            <li><strong>Tenant Isolation:</strong> Multi-tenant data is isolated using Row-Level Security</li>
            <li><strong>Audit Logging:</strong> All significant actions are logged for security monitoring</li>
            <li><strong>Secure Authentication:</strong> Passwords are hashed using bcrypt; optional MFA available</li>
          </ul>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">5. Data Retention</h2>
          <p className="text-slate-600 mb-4">
            We retain your data as follows:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li><strong>Active Accounts:</strong> Data is retained for the duration of your subscription</li>
            <li><strong>Cancelled Accounts:</strong> After cancellation, you may request data export. Data is retained for a grace period, then deleted</li>
            <li><strong>Audit Logs:</strong> Security and audit logs may be retained longer for compliance purposes</li>
            <li><strong>Backups:</strong> Automated backups are retained according to our backup policy and deleted on a rolling basis</li>
          </ul>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">6. Your Rights</h2>
          <p className="text-slate-600 mb-4">
            You have the following rights regarding your personal data:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li><strong>Access:</strong> Request a copy of your personal data</li>
            <li><strong>Correction:</strong> Update or correct inaccurate data</li>
            <li><strong>Deletion:</strong> Request deletion of your data (subject to legal retention requirements)</li>
            <li><strong>Export:</strong> Export your data in a machine-readable format</li>
            <li><strong>Objection:</strong> Object to certain processing of your data</li>
          </ul>
          <p className="text-slate-600 mb-4">
            To exercise these rights, contact us at{' '}
            <a href="mailto:privacy@pearl.app" className="text-teal-600 hover:underline">privacy@pearl.app</a>.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">7. Cookies and Tracking</h2>
          <p className="text-slate-600 mb-4">
            We use essential cookies to operate the Service:
          </p>
          <ul className="list-disc pl-6 text-slate-600 mb-4 space-y-2">
            <li><strong>Authentication Cookies:</strong> Keep you logged in during your session</li>
            <li><strong>Security Cookies:</strong> Help prevent fraud and protect your account</li>
            <li><strong>Preference Cookies:</strong> Remember your settings and preferences</li>
          </ul>
          <p className="text-slate-600 mb-4">
            We do not use third-party advertising or tracking cookies.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">8. International Data Transfers</h2>
          <p className="text-slate-600 mb-4">
            Your data may be processed in countries other than your own. Our hosting providers maintain
            appropriate safeguards for international data transfers, including compliance with applicable
            data protection laws.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">9. Children's Privacy</h2>
          <p className="text-slate-600 mb-4">
            The Service is not intended for users under 18 years of age. We do not knowingly collect
            personal information from children. If we become aware that we have collected data from a
            child, we will take steps to delete it.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">10. Changes to This Policy</h2>
          <p className="text-slate-600 mb-4">
            We may update this Privacy Policy from time to time. We will notify you of material changes
            by email or through a notice on the Service. Your continued use of the Service after such
            changes constitutes acceptance of the updated policy.
          </p>

          <h2 className="text-2xl font-semibold text-slate-900 mt-8 mb-4">11. Contact Us</h2>
          <p className="text-slate-600 mb-4">
            If you have questions about this Privacy Policy or our data practices, please contact us:
          </p>
          <ul className="list-none text-slate-600 mb-4 space-y-1">
            <li>Email: <a href="mailto:privacy@pearl.app" className="text-teal-600 hover:underline">privacy@pearl.app</a></li>
            <li>General inquiries: <a href="mailto:support@pearl.app" className="text-teal-600 hover:underline">support@pearl.app</a></li>
          </ul>
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
