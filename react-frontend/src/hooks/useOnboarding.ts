/**
 * Onboarding hook
 *
 * Manages onboarding wizard state for new tenant admins.
 * Shows QuickStartWizard for admins with no studies, or OnboardingWizard for those who have data.
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getOnboardingStatus, completeOnboarding } from '@/api/endpoints/tenant-data';
import { useAuthStore } from '@/stores/authStore';
import { studiesApi } from '@/api';

const LOCAL_STORAGE_KEY = 'pearl-onboarding-completed';

// Helper to check if onboarding was completed locally (as fallback)
function getLocalOnboardingCompleted(): boolean {
  try {
    return localStorage.getItem(LOCAL_STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

// Helper to mark onboarding as completed locally
function setLocalOnboardingCompleted(): void {
  try {
    localStorage.setItem(LOCAL_STORAGE_KEY, 'true');
  } catch {
    // Ignore localStorage errors
  }
}

export function useOnboarding() {
  const queryClient = useQueryClient();
  const { currentUser } = useAuthStore();
  const [showWizard, setShowWizard] = useState(false);

  // Only check onboarding status for admin users
  const shouldCheckOnboarding = currentUser?.is_admin === true;

  // Fetch onboarding status
  const { data: status, isLoading, error } = useQuery({
    queryKey: ['onboardingStatus'],
    queryFn: getOnboardingStatus,
    enabled: shouldCheckOnboarding,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Fetch studies to determine if user has any data
  const { data: studies = [] } = useQuery({
    queryKey: ['studies'],
    queryFn: studiesApi.getAll,
    enabled: shouldCheckOnboarding,
    staleTime: 5 * 60 * 1000,
  });

  // Complete onboarding mutation
  const completeMutation = useMutation({
    mutationFn: completeOnboarding,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboardingStatus'] });
      setShowWizard(false);
    },
  });

  // Determine if user has studies
  const hasStudies = studies.length > 0;

  // Show wizard for admins who haven't completed onboarding
  // Also check localStorage as fallback (in case API call failed previously)
  useEffect(() => {
    if (shouldCheckOnboarding && status) {
      const locallyCompleted = getLocalOnboardingCompleted();
      if (!status.onboarding_completed && !locallyCompleted) {
        setShowWizard(true);
      }
    }
  }, [status, shouldCheckOnboarding]);

  const handleComplete = useCallback(() => {
    // Immediately dismiss the wizard for better UX
    setShowWizard(false);
    // Save to localStorage as backup (in case API fails)
    setLocalOnboardingCompleted();
    // Then persist to backend (fire-and-forget)
    completeMutation.mutate();
  }, [completeMutation]);

  const handleSkip = useCallback(() => {
    // Immediately dismiss the wizard for better UX
    setShowWizard(false);
    // Save to localStorage as backup (in case API fails)
    setLocalOnboardingCompleted();
    // Skip also marks onboarding as complete
    completeMutation.mutate();
  }, [completeMutation]);

  const dismissWizard = useCallback(() => {
    // Just dismiss without marking as complete (will show again on next login)
    setShowWizard(false);
  }, []);

  return {
    showWizard,
    isLoading,
    error,
    onboardingCompleted: status?.onboarding_completed ?? true,
    hasStudies,
    handleComplete,
    handleSkip,
    dismissWizard,
    isCompleting: completeMutation.isPending,
  };
}
