/**
 * Onboarding Provider
 *
 * Renders the appropriate onboarding wizard for new tenant admins when appropriate.
 * - QuickStartWizard: For admins with no studies (guides them through creating first study)
 * - OnboardingWizard: For admins who already have data (informational slides)
 *
 * Should be placed inside the authenticated app shell.
 */

import { useOnboarding } from '@/hooks/useOnboarding';
import { OnboardingWizard } from './OnboardingWizard';
import { QuickStartWizard } from './QuickStartWizard';

interface OnboardingProviderProps {
  children: React.ReactNode;
}

export function OnboardingProvider({ children }: OnboardingProviderProps) {
  const { showWizard, hasStudies, handleComplete, handleSkip, dismissWizard } = useOnboarding();

  return (
    <>
      {children}
      {showWizard && (
        // Show QuickStart wizard if no studies, otherwise show info wizard
        !hasStudies ? (
          <QuickStartWizard
            onComplete={handleComplete}
            onSkip={handleSkip}
            onDismiss={dismissWizard}
          />
        ) : (
          <OnboardingWizard
            onComplete={handleComplete}
            onSkip={handleSkip}
            onDismiss={dismissWizard}
          />
        )
      )}
    </>
  );
}
