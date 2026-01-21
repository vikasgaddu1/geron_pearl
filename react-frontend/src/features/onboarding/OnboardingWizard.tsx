/**
 * Onboarding Wizard
 * 
 * Multi-step wizard shown to new tenant admins on first login.
 * Guides them through initial setup and key features.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  Check,
  BookOpen,
  Users,
  Package,
  BarChart3,
  Sparkles,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';

interface OnboardingWizardProps {
  onComplete: () => void;
  onSkip?: () => void;
  onDismiss?: () => void;
}

const STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to PEARL!',
    subtitle: 'Track, collaborate, deliver',
    icon: Sparkles,
    content: (
      <div className="text-center space-y-4">
        <p className="text-gray-600">
          Your team's command center for SDTM, ADaM, and TFL deliverables. Assign work,
          track progress, and hit your deadlines — all in one place.
        </p>
        <p className="text-gray-600">
          Let's take a quick tour to get you started.
        </p>
        <div className="pt-4 flex justify-center">
          <div className="w-32 h-32 bg-teal-600 rounded-full flex items-center justify-center">
            <span className="text-5xl text-white font-bold">P</span>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: 'studies',
    title: 'Studies & Releases',
    subtitle: 'Organize your clinical trials',
    icon: BookOpen,
    content: (
      <div className="space-y-4">
        <p className="text-gray-600">
          Start by creating <strong>Studies</strong> for each clinical trial you're working on.
        </p>
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-teal-100 text-teal-600 flex items-center justify-center text-sm font-medium">1</div>
            <div>
              <p className="font-medium">Create a Study</p>
              <p className="text-sm text-gray-500">Each study has a unique label (e.g., "STUDY-001")</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-teal-100 text-teal-600 flex items-center justify-center text-sm font-medium">2</div>
            <div>
              <p className="font-medium">Add Database Releases</p>
              <p className="text-sm text-gray-500">Each release represents a data snapshot (interim, final)</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-teal-100 text-teal-600 flex items-center justify-center text-sm font-medium">3</div>
            <div>
              <p className="font-medium">Create Reporting Efforts</p>
              <p className="text-sm text-gray-500">Group your deliverables by purpose (CSR, FDA submission)</p>
            </div>
          </div>
        </div>
        <p className="text-sm text-gray-500 italic">
          We've added sample studies (DEMO-001, DEMO-002) to help you explore.
        </p>
      </div>
    ),
  },
  {
    id: 'packages',
    title: 'TFL Packages',
    subtitle: 'Manage your deliverables',
    icon: Package,
    content: (
      <div className="space-y-4">
        <p className="text-gray-600">
          <strong>Packages</strong> organize your Tables, Figures, Listings, and Datasets.
        </p>
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-3">
            <Check className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <p className="font-medium">Tables, Listings, Figures (TLFs)</p>
              <p className="text-sm text-gray-500">Standard clinical trial outputs</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Check className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <p className="font-medium">Datasets (SDTM, ADaM)</p>
              <p className="text-sm text-gray-500">Source data for your analyses</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Check className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <p className="font-medium">Text Elements</p>
              <p className="text-sm text-gray-500">Reusable titles, footnotes, populations, acronyms</p>
            </div>
          </div>
        </div>
        <p className="text-sm text-gray-500 italic">
          Sample packages (PKG-SAFETY, PKG-EFFICACY, PKG-DEMOGRAPHICS) are ready to explore.
        </p>
      </div>
    ),
  },
  {
    id: 'tracker',
    title: 'Production Tracker',
    subtitle: 'Track progress in real-time',
    icon: BarChart3,
    content: (
      <div className="space-y-4">
        <p className="text-gray-600">
          The <strong>Tracker</strong> shows production and QC status for every item.
        </p>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="font-medium">Workflow Status</span>
          </div>
          <div className="flex gap-2 flex-wrap">
            <span className="px-2 py-1 rounded text-xs bg-gray-200 text-gray-700">Not Started</span>
            <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-700">In Progress</span>
            <span className="px-2 py-1 rounded text-xs bg-yellow-100 text-yellow-700">Ready for QC</span>
            <span className="px-2 py-1 rounded text-xs bg-purple-100 text-purple-700">QC In Progress</span>
            <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-700">Completed</span>
          </div>
        </div>
        <div className="space-y-2 text-sm text-gray-600">
          <p>• Assign Production and QC programmers to each item</p>
          <p>• Track due dates and prioritize work</p>
          <p>• Add comments and resolve issues</p>
          <p>• See real-time updates from your team</p>
        </div>
      </div>
    ),
  },
  {
    id: 'team',
    title: 'Team Management',
    subtitle: 'Collaborate with your team',
    icon: Users,
    content: (
      <div className="space-y-4">
        <p className="text-gray-600">
          Add team members and control access with <strong>role-based permissions</strong>.
        </p>
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-16 text-xs font-medium text-teal-600">ADMIN</div>
            <p className="text-sm text-gray-600">Full access to all features and settings</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-16 text-xs font-medium text-amber-600">RESPONSIBLE</div>
            <p className="text-sm text-gray-600">Full admin access within assigned studies</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-16 text-xs font-medium text-blue-600">EDITOR</div>
            <p className="text-sm text-gray-600">Edit tracker data in assigned studies</p>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-16 text-xs font-medium text-gray-600">VIEWER</div>
            <p className="text-sm text-gray-600">Read-only access to assigned studies</p>
          </div>
        </div>
        <p className="text-sm text-gray-500">
          Go to <strong>User Management</strong> to add your team members.
        </p>
      </div>
    ),
  },
  {
    id: 'complete',
    title: "You're All Set!",
    subtitle: 'Start exploring PEARL',
    icon: Check,
    content: (
      <div className="text-center space-y-4">
        <div className="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center">
          <Check className="w-10 h-10 text-green-600" />
        </div>
        <p className="text-gray-600">
          You're ready to start using PEARL! Explore the sample data we've 
          created, or jump right in and create your own studies.
        </p>
        <div className="pt-4 space-y-2 text-sm text-gray-500">
          <p>Need help? Check out the <strong>Help Center</strong> anytime.</p>
          <p>You can always reset to sample data from <strong>Settings</strong>.</p>
        </div>
      </div>
    ),
  },
];

export function OnboardingWizard({ onComplete, onSkip, onDismiss }: OnboardingWizardProps) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [dontShowAgain, setDontShowAgain] = useState(true);

  const step = STEPS[currentStep];
  const progress = ((currentStep + 1) / STEPS.length) * 100;
  const isLastStep = currentStep === STEPS.length - 1;
  const isFirstStep = currentStep === 0;

  const handleNext = () => {
    if (isLastStep) {
      handleComplete();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(0, prev - 1));
  };

  const handleComplete = () => {
    // Call the onComplete callback - the parent (OnboardingProvider) handles the API call
    onComplete();
    navigate('/app/dashboard');
  };

  const handleSkip = () => {
    if (dontShowAgain) {
      // Mark as complete so it won't show again
      if (onSkip) {
        onSkip();
      } else {
        onComplete();
      }
    } else {
      // Just dismiss temporarily (will show again next login)
      if (onDismiss) {
        onDismiss();
      }
    }
    navigate('/app/dashboard');
  };

  const Icon = step.icon;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg bg-white shadow-2xl">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">P</span>
            </div>
            <span className="text-sm text-gray-500">
              Step {currentStep + 1} of {STEPS.length}
            </span>
          </div>
          {!isLastStep && (
            <Button variant="ghost" size="sm" onClick={handleSkip} className="text-gray-400">
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Progress */}
        <Progress value={progress} className="h-1 rounded-none" />

        {/* Content */}
        <CardContent className="p-6">
          <div className="text-center mb-6">
            <div className="w-12 h-12 mx-auto mb-4 bg-teal-100 rounded-full flex items-center justify-center">
              <Icon className="w-6 h-6 text-teal-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900">{step.title}</h2>
            <p className="text-gray-500">{step.subtitle}</p>
          </div>

          <div className="min-h-[280px]">
            {step.content}
          </div>
        </CardContent>

        {/* Footer */}
        <div className="p-4 border-t space-y-3">
          {/* Don't show again checkbox - only show when not on last step */}
          {!isLastStep && (
            <div className="flex items-center justify-center gap-2">
              <Checkbox
                id="dont-show-again"
                checked={dontShowAgain}
                onCheckedChange={(checked) => setDontShowAgain(checked === true)}
              />
              <Label
                htmlFor="dont-show-again"
                className="text-sm text-gray-500 cursor-pointer"
              >
                Don't show this again
              </Label>
            </div>
          )}

          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={isFirstStep}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>

            <div className="flex gap-2">
              {!isLastStep && (
                <Button variant="ghost" onClick={handleSkip}>
                  Skip Tour
                </Button>
              )}
              <Button onClick={handleNext}>
                {isLastStep ? (
                  <>
                    Get Started
                    <Check className="h-4 w-4 ml-2" />
                  </>
                ) : (
                  <>
                    Next
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
