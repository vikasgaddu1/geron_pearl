/**
 * Quick Start Wizard
 *
 * Interactive wizard that guides new admin users through creating
 * their first study, database release, and optionally a package.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { useQuickStartWizard } from './hooks/useQuickStartWizard';
import { StudyStep } from './steps/StudyStep';
import { DatabaseReleaseStep } from './steps/DatabaseReleaseStep';
import { PackageStep } from './steps/PackageStep';
import { CompletionStep } from './steps/CompletionStep';
import { getErrorMessage } from '@/lib/utils';

interface QuickStartWizardProps {
  onComplete: () => void;
  onSkip?: () => void;
  onDismiss?: () => void;
}

const STEPS = ['Create Study', 'Add Release', 'Add Package', 'Complete'];

export function QuickStartWizard({ onComplete, onSkip, onDismiss }: QuickStartWizardProps) {
  const navigate = useNavigate();
  const [dontShowAgain, setDontShowAgain] = useState(true);

  const {
    currentStep,
    createdStudy,
    createdRelease,
    createdPackage,
    createStudyMutation,
    createReleaseMutation,
    createPackageMutation,
    skipPackageStep,
  } = useQuickStartWizard();

  const progress = ((currentStep + 1) / STEPS.length) * 100;

  const handleSkipWizard = () => {
    if (dontShowAgain && onSkip) {
      onSkip();
    } else if (onDismiss) {
      onDismiss();
    }
    navigate('/app/dashboard');
  };

  const handleComplete = () => {
    onComplete();
    navigate('/app/dashboard');
  };

  const handleGoToStudyManagement = () => {
    onComplete();
    navigate('/app/study-management');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg bg-white shadow-2xl">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">P</span>
            </div>
            <div>
              <span className="text-sm font-medium">Quick Start</span>
              <span className="text-xs text-gray-500 ml-2">
                Step {currentStep + 1} of {STEPS.length}
              </span>
            </div>
          </div>
          {currentStep < 3 && (
            <Button variant="ghost" size="sm" onClick={handleSkipWizard} className="text-gray-400">
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Progress */}
        <Progress value={progress} className="h-1 rounded-none" />

        {/* Step indicators */}
        <div className="px-4 py-3 border-b">
          <div className="flex justify-between">
            {STEPS.map((step, index) => (
              <div key={step} className="flex items-center">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                    index < currentStep
                      ? 'bg-teal-600 text-white'
                      : index === currentStep
                        ? 'bg-teal-100 text-teal-600 border-2 border-teal-600'
                        : 'bg-gray-100 text-gray-400'
                  }`}
                >
                  {index < currentStep ? '\u2713' : index + 1}
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={`w-8 h-0.5 mx-1 ${
                      index < currentStep ? 'bg-teal-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <CardContent className="p-6 min-h-[400px]">
          {currentStep === 0 && (
            <StudyStep
              onSubmit={(data) => createStudyMutation.mutate(data)}
              isLoading={createStudyMutation.isPending}
              error={createStudyMutation.error ? getErrorMessage(createStudyMutation.error) : undefined}
            />
          )}

          {currentStep === 1 && createdStudy && (
            <DatabaseReleaseStep
              study={createdStudy}
              onSubmit={(data) => createReleaseMutation.mutate(data)}
              isLoading={createReleaseMutation.isPending}
              error={createReleaseMutation.error ? getErrorMessage(createReleaseMutation.error) : undefined}
            />
          )}

          {currentStep === 2 && (
            <PackageStep
              onSubmit={(data) => createPackageMutation.mutate(data)}
              onSkip={skipPackageStep}
              isLoading={createPackageMutation.isPending}
              error={createPackageMutation.error ? getErrorMessage(createPackageMutation.error) : undefined}
            />
          )}

          {currentStep === 3 && createdStudy && createdRelease && (
            <CompletionStep
              study={createdStudy}
              release={createdRelease}
              pkg={createdPackage}
              onComplete={handleComplete}
              onGoToStudyManagement={handleGoToStudyManagement}
            />
          )}
        </CardContent>

        {/* Footer - Skip option */}
        {currentStep < 3 && (
          <div className="p-4 border-t">
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
                Don't show this wizard again
              </Label>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSkipWizard}
              className="w-full mt-2 text-gray-500"
            >
              Skip wizard and create manually later
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
