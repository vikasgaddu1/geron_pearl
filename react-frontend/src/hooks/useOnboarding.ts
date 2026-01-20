/**
 * Onboarding hook
 * 
 * Manages onboarding wizard state for new tenant admins.
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getOnboardingStatus, completeOnboarding } from '@/api/endpoints/tenant-data';
import { useAuthStore } from '@/stores/authStore';

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

  // Complete onboarding mutation
  const completeMutation = useMutation({
    mutationFn: completeOnboarding,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboardingStatus'] });
      setShowWizard(false);
    },
  });

  // Show wizard for admins who haven't completed onboarding
  useEffect(() => {
    if (status && !status.onboarding_completed && shouldCheckOnboarding) {
      setShowWizard(true);
    }
  }, [status, shouldCheckOnboarding]);

  const handleComplete = useCallback(() => {
    completeMutation.mutate();
  }, [completeMutation]);

  const handleSkip = useCallback(() => {
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
    sampleDataSeeded: status?.sample_data_seeded ?? false,
    handleComplete,
    handleSkip,
    dismissWizard,
    isCompleting: completeMutation.isPending,
  };
}
