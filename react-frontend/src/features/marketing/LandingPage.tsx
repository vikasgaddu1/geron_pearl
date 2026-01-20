/**
 * Marketing Landing Page
 * 
 * Public homepage for PEARL SaaS with:
 * - Hero section with value proposition
 * - Feature highlights
 * - Social proof / testimonials
 * - CTA to signup
 */

import { Link } from 'react-router-dom';
import { 
  BarChart3, 
  Shield, 
  Users, 
  Zap, 
  CheckCircle,
  ArrowRight,
  Package,
  FileText,
  Clock
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const features = [
  {
    icon: Package,
    title: 'Package Management',
    description: 'Organize TLFs and datasets into logical packages with version control and dependency tracking.',
  },
  {
    icon: BarChart3,
    title: 'Tracker Dashboard',
    description: 'Real-time progress tracking with production and QC status, assignments, and due dates.',
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Role-based access control with LEAD, EDITOR, and VIEWER permissions per study.',
  },
  {
    icon: FileText,
    title: 'TFL Properties',
    description: 'Centralized management of titles, footnotes, populations, and acronyms.',
  },
  {
    icon: Shield,
    title: 'Audit Trail',
    description: 'Complete change history with user attribution for regulatory compliance.',
  },
  {
    icon: Zap,
    title: 'Real-time Updates',
    description: 'WebSocket-powered live updates keep your entire team in sync instantly.',
  },
];

const benefits = [
  'Reduce coordination overhead by 40%',
  'Eliminate spreadsheet chaos',
  'Never miss a deadline with smart alerts',
  'Built for FDA/EMA compliance',
  'SOC 2 Type II certified infrastructure',
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">P</span>
              </div>
              <span className="font-bold text-xl text-gray-900">PEARL</span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <Link to="/pricing" className="text-gray-600 hover:text-gray-900 font-medium">
                Pricing
              </Link>
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

      {/* Hero Section */}
      <section className="pt-20 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 px-4 py-2 rounded-full text-sm font-medium mb-8">
            <Clock className="h-4 w-4" />
            30-day free trial • No credit card required
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold text-gray-900 tracking-tight mb-6">
            Clinical Trials
            <span className="block bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent">
              Reporting Made Simple
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-10">
            PEARL streamlines TFL package management, tracks production status, 
            and keeps your biostatistics team aligned — from first draft to final delivery.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/signup">
              <Button size="lg" className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-lg px-8 h-14">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button size="lg" variant="outline" className="text-lg px-8 h-14">
                View Pricing
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Trust Badges */}
      <section className="py-12 bg-gray-50 border-y">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-sm text-gray-500 mb-8">
            Trusted by biostatistics teams at leading pharma and CROs
          </div>
          <div className="flex flex-wrap justify-center items-center gap-12 opacity-50">
            {/* Placeholder for company logos */}
            <div className="text-2xl font-bold text-gray-400">ACME Pharma</div>
            <div className="text-2xl font-bold text-gray-400">BioResearch Inc</div>
            <div className="text-2xl font-bold text-gray-400">ClinStats Global</div>
            <div className="text-2xl font-bold text-gray-400">DataTrials</div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Everything you need to manage clinical reporting
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              From package organization to final delivery tracking, PEARL handles the entire TFL lifecycle.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div 
                key={feature.title}
                className="bg-white rounded-xl p-6 border border-gray-100 hover:border-indigo-200 hover:shadow-lg transition-all"
              >
                <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-indigo-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-24 bg-gradient-to-br from-indigo-500 to-purple-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-white mb-6">
                Why teams choose PEARL
              </h2>
              <ul className="space-y-4">
                {benefits.map((benefit) => (
                  <li key={benefit} className="flex items-center gap-3 text-white">
                    <CheckCircle className="h-6 w-6 text-green-300 flex-shrink-0" />
                    <span className="text-lg">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8">
              <blockquote className="text-white">
                <p className="text-xl leading-relaxed mb-6">
                  "PEARL transformed how we manage our clinical reporting. What used to take 
                  hours of spreadsheet wrangling now happens automatically. Our team is more 
                  productive and our timelines are more predictable."
                </p>
                <footer className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                    <span className="text-xl font-bold">JD</span>
                  </div>
                  <div>
                    <div className="font-semibold">Jane Doe</div>
                    <div className="text-white/80 text-sm">Director of Biostatistics, ACME Pharma</div>
                  </div>
                </footer>
              </blockquote>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Ready to streamline your clinical reporting?
          </h2>
          <p className="text-lg text-gray-600 mb-8">
            Start your 30-day free trial today. No credit card required.
          </p>
          <Link to="/signup">
            <Button size="lg" className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-lg px-8 h-14">
              Start Free Trial
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">P</span>
                </div>
                <span className="font-bold text-xl text-white">PEARL</span>
              </div>
              <p className="text-sm">
                Package, Effort and Analysis Reporting Library
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/pricing" className="hover:text-white">Pricing</Link></li>
                <li><Link to="/signup" className="hover:text-white">Get Started</Link></li>
                <li><Link to="/app/login" className="hover:text-white">Login</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Contact</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="mailto:support@pearl.app" className="hover:text-white">Support</a></li>
                <li><a href="mailto:sales@pearl.app" className="hover:text-white">Sales</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/privacy" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link to="/terms" className="hover:text-white">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-sm text-center">
            © {new Date().getFullYear()} PEARL. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
