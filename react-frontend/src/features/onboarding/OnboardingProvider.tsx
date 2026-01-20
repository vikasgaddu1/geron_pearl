/**
 * Onboarding Provider
 * 
 * Renders the onboarding wizard for new tenant admins when appropriate.
 * Should be placed inside the authenticated app shell.
 */

import { useOnboarding } from '@/hooks/useOnboarding';
import { OnboardingWizard } from './OnboardingWizard';

interface OnboardingProviderProps {
  children: React.ReactNode;
}

export function OnboardingProvider({ children }: OnboardingProviderProps) {
  const { showWizard, handleComplete, handleSkip } = useOnboarding();

  return (
    <>
      {children}
      {showWizard && (
        <OnboardingWizard 
          onComplete={handleComplete} 
          onSkip={handleSkip}
        />
      )}
    </>
  );
}
