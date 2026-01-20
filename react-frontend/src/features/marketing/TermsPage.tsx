/**
 * Terms of Service Page
 * 
 * Placeholder legal page for Terms of Service
 */

import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export function TermsPage() {
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
            <Link 
              to="/" 
              className="text-gray-600 hover:text-gray-900 font-medium flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Home
            </Link>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-3xl mx-auto px-4 py-16">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Terms of Service</h1>
        
        <div className="prose prose-gray max-w-none">
          <p className="text-gray-600 mb-6">
            <em>Last updated: January 20, 2026</em>
          </p>

          <h2 className="text-2xl font-semibold text-gray-900 mt-8 mb-4">1. Acceptance of Terms</h2>
          <p className="text-gray-600 mb-4">
            By accessing and using PEARL ("the Service"), you accept and agree to be bound by the terms 
            and provision of this agreement.
          </p>

          <h2 className="text-2xl font-semibold text-gray-900 mt-8 mb-4">2. Description of Service</h2>
          <p className="text-gray-600 mb-4">
            PEARL provides a clinical research data management platform for biostatistics teams 
            to manage TFL packages, track production status, and collaborate on reporting efforts.
          </p>

          <h2 className="text-2xl font-semibold text-gray-900 mt-8 mb-4">3. User Accounts</h2>
          <p className="text-gray-600 mb-4">
            You are responsible for maintaining the confidentiality of your account credentials 
            and for all activities that occur under your account.
          </p>

          <h2 className="text-2xl font-semibold text-gray-900 mt-8 mb-4">4. Data Privacy</h2>
          <p className="text-gray-600 mb-4">
            Your use of the Service is also governed by our Privacy Policy. Please review our 
            Privacy Policy to understand our practices.
          </p>

          <h2 className="text-2xl font-semibold text-gray-900 mt-8 mb-4">5. Subscription and Billing</h2>
          <p className="text-gray-600 mb-4">
            Paid subscriptions are billed in advance on a monthly or annual basis. 
            You may cancel your subscription at any time.
          </p>

          <h2 className="text-2xl font-semibold text-gray-900 mt-8 mb-4">6. Contact</h2>
          <p className="text-gray-600 mb-4">
            For any questions about these Terms, please contact us at{' '}
            <a href="mailto:legal@pearl.app" className="text-indigo-600 hover:underline">
              legal@pearl.app
            </a>
          </p>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8 px-4 text-center text-sm">
        © {new Date().getFullYear()} PEARL. All rights reserved.
      </footer>
    </div>
  );
}
