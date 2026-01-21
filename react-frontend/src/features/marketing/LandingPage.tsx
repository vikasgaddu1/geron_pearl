/**
 * Marketing Landing Page
 *
 * Clean clinical design for PEARL SaaS:
 * - Professional teal/slate color palette
 * - Sharp typography, no gradient text
 * - Solid buttons, no glowing effects
 * - Data-focused, enterprise pharma aesthetic
 */

import { Link } from 'react-router-dom';
import {
  BarChart3,
  Shield,
  Users,
  Zap,
  ArrowRight,
  Package,
  FileText,
  Clock,
  Database,
  Lock,
  TrendingUp
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

const features = [
  {
    icon: Package,
    title: 'Package Management',
    description: 'Organize TLFs and datasets into logical packages with version control and dependency tracking.',
    stat: '60%',
    statLabel: 'faster organization',
  },
  {
    icon: BarChart3,
    title: 'Tracker Dashboard',
    description: 'Real-time progress tracking with production and QC status, assignments, and due dates.',
    stat: '100%',
    statLabel: 'visibility',
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Role-based access control with LEAD, BIOSTAT, EDITOR, and VIEWER permissions per study.',
    stat: '40%',
    statLabel: 'less overhead',
  },
  {
    icon: FileText,
    title: 'TFL Properties',
    description: 'Centralized management of titles, footnotes, populations, and acronyms.',
    stat: '0',
    statLabel: 'inconsistencies',
  },
  {
    icon: Shield,
    title: 'Audit Trail',
    description: 'Complete change history with user attribution for regulatory compliance.',
    stat: '21 CFR',
    statLabel: 'Part 11 ready',
  },
  {
    icon: Zap,
    title: 'Real-time Updates',
    description: 'WebSocket-powered live updates keep your entire team in sync instantly.',
    stat: '<1s',
    statLabel: 'sync time',
  },
];

const benefits = [
  { text: 'Reduce coordination overhead by 40%', icon: TrendingUp },
  { text: 'Eliminate spreadsheet chaos', icon: Database },
  { text: 'Never miss a deadline with smart alerts', icon: Clock },
  { text: 'Built for FDA/EMA compliance', icon: Shield },
  { text: 'SOC 2 Type II certified infrastructure', icon: Lock },
];

const metrics = [
  { value: '50+', label: 'Clinical teams' },
  { value: '10K+', label: 'TLFs managed' },
  { value: '99.9%', label: 'Uptime SLA' },
  { value: '<2hr', label: 'Support response' },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-slate-200 bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link to="/" className="flex items-center gap-3 group">
                    <div className="w-9 h-9 bg-teal-600 rounded-lg flex items-center justify-center group-hover:bg-teal-700 transition-colors">
                      <span className="text-white font-bold text-lg">P</span>
                    </div>
                    <span className="font-semibold text-xl text-slate-900 tracking-tight">PEARL</span>
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-xs">
                  <p className="font-semibold">Package, Effort, and Analysis Reporting Library</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Your team's command center for study deliverables
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <div className="hidden md:flex items-center gap-8">
              <Link to="/pricing" className="text-slate-600 hover:text-slate-900 font-medium text-sm">
                Pricing
              </Link>
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

      {/* Hero Section */}
      <section className="pt-16 pb-24 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 bg-teal-50 text-teal-700 px-3 py-1.5 rounded-full text-sm font-medium mb-6 border border-teal-200">
              <Clock className="h-4 w-4" />
              30-day free trial — No credit card required
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 tracking-tight mb-6 leading-[1.1]">
              Clinical reporting
              <span className="block text-teal-600">
                without the chaos
              </span>
            </h1>
            <p className="text-sm text-slate-500 mb-4 font-medium">
              PEARL — Package, Effort and Analysis Reporting Library
            </p>
            <p className="text-lg sm:text-xl text-slate-600 mb-8 leading-relaxed">
              Streamline your SDTM, ADaM, and TFL package management, track production status,
              and keep your biostatistics team aligned—from first draft to final delivery.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link to="/signup">
                <Button size="lg" className="bg-teal-600 hover:bg-teal-700 text-white font-medium text-base px-6 h-12 w-full sm:w-auto">
                  Start Free Trial
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
              <Link to="/pricing">
                <Button size="lg" variant="outline" className="border-slate-300 text-slate-700 hover:bg-slate-100 font-medium text-base px-6 h-12 w-full sm:w-auto">
                  View Pricing
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Metrics Bar */}
      <section className="py-8 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {metrics.map((metric) => (
              <div key={metric.label} className="text-center">
                <div className="text-2xl sm:text-3xl font-bold text-slate-900">{metric.value}</div>
                <div className="text-sm text-slate-500 mt-1">{metric.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust Badges */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-sm text-slate-500 mb-8 font-medium uppercase tracking-wide">
            Trusted by biostatistics teams at
          </div>
          <div className="flex flex-wrap justify-center items-center gap-x-12 gap-y-6">
            <div className="text-xl font-semibold text-slate-300">Pharmaceutical Companies</div>
            <div className="text-xl font-semibold text-slate-300">Contract Research Organizations</div>
            <div className="text-xl font-semibold text-slate-300">Biotech Firms</div>
            <div className="text-xl font-semibold text-slate-300">Academic Medical Centers</div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              Everything you need for clinical reporting
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              From package organization to final delivery tracking, PEARL handles the entire TFL lifecycle.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="bg-white rounded-lg p-6 border border-slate-200 hover:border-teal-300 hover:shadow-md transition-all group"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 bg-teal-50 rounded-lg flex items-center justify-center group-hover:bg-teal-100 transition-colors">
                    <feature.icon className="h-5 w-5 text-teal-600" />
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-slate-900">{feature.stat}</div>
                    <div className="text-xs text-slate-500">{feature.statLabel}</div>
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-slate-600 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-white mb-8">
                Why teams choose PEARL
              </h2>
              <ul className="space-y-5">
                {benefits.map((benefit) => (
                  <li key={benefit.text} className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-lg bg-teal-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <benefit.icon className="h-4 w-4 text-teal-400" />
                    </div>
                    <span className="text-lg text-slate-300">{benefit.text}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-slate-800 rounded-xl p-8 border border-slate-700">
              <blockquote>
                <p className="text-lg text-slate-300 leading-relaxed mb-6">
                  "PEARL transformed how we manage our clinical reporting. What used to take
                  hours of spreadsheet wrangling now happens automatically. Our team is more
                  productive and our timelines are more predictable."
                </p>
                <footer className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center">
                    <span className="text-lg font-semibold text-slate-300">DB</span>
                  </div>
                  <div>
                    <div className="font-semibold text-white">Director of Biostatistics</div>
                    <div className="text-slate-400 text-sm">Top 10 Pharmaceutical Company</div>
                  </div>
                </footer>
              </blockquote>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              Get started in minutes
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              No complex setup. Import your existing data and start tracking immediately.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Create your workspace', desc: 'Set up your organization and invite your team members with role-based permissions.' },
              { step: '02', title: 'Import your studies', desc: 'Upload existing TFL lists or create new studies from scratch with our intuitive interface.' },
              { step: '03', title: 'Track in real-time', desc: 'Monitor progress, manage assignments, and hit every deadline with live dashboards.' },
            ].map((item) => (
              <div key={item.step} className="relative">
                <div className="text-6xl font-bold text-slate-100 mb-4">{item.step}</div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{item.title}</h3>
                <p className="text-slate-600 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-teal-600">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to streamline your clinical reporting?
          </h2>
          <p className="text-lg text-teal-100 mb-8">
            Start your 30-day free trial today. No credit card required.
          </p>
          <Link to="/signup">
            <Button size="lg" className="bg-white text-teal-700 hover:bg-teal-50 font-medium text-base px-8 h-12">
              Start Free Trial
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 bg-teal-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">P</span>
                </div>
                <span className="font-semibold text-xl text-white">PEARL</span>
              </div>
              <p className="text-sm leading-relaxed">
                Package, Effort and Analysis<br />Reporting Library
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4 text-sm">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/pricing" className="hover:text-white transition-colors">Pricing</Link></li>
                <li><Link to="/signup" className="hover:text-white transition-colors">Get Started</Link></li>
                <li><Link to="/app/login" className="hover:text-white transition-colors">Sign in</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4 text-sm">Contact</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="mailto:support@pearl.app" className="hover:text-white transition-colors">Support</a></li>
                <li><a href="mailto:sales@pearl.app" className="hover:text-white transition-colors">Sales</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4 text-sm">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
                <li><Link to="/terms" className="hover:text-white transition-colors">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-800 pt-8 text-sm text-center">
            © {new Date().getFullYear()} PEARL. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
