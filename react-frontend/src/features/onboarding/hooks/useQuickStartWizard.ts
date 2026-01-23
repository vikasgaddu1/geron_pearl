/**
 * Custom hook for Quick Start wizard state management
 */

import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { studiesApi, databaseReleasesApi, packagesApi } from '@/api';
import type { Study, DatabaseRelease, Package } from '@/types';
import type { StudyFormData, DatabaseReleaseFormData, PackageFormData } from '../schemas/quickStartSchemas';

interface WizardState {
  currentStep: number;
  createdStudy: Study | null;
  createdRelease: DatabaseRelease | null;
  createdPackage: Package | null;
  skipPackage: boolean;
}

export function useQuickStartWizard() {
  const queryClient = useQueryClient();

  const [state, setState] = useState<WizardState>({
    currentStep: 0,
    createdStudy: null,
    createdRelease: null,
    createdPackage: null,
    skipPackage: false,
  });

  // Study creation mutation
  const createStudyMutation = useMutation({
    mutationFn: (data: StudyFormData) => studiesApi.create(data),
    onSuccess: (study) => {
      queryClient.invalidateQueries({ queryKey: ['studies'] });
      setState(prev => ({ ...prev, createdStudy: study, currentStep: 1 }));
    },
  });

  // Database release creation mutation
  const createReleaseMutation = useMutation({
    mutationFn: (data: DatabaseReleaseFormData & { study_id: number }) =>
      databaseReleasesApi.create(data),
    onSuccess: (release) => {
      queryClient.invalidateQueries({ queryKey: ['database-releases'] });
      setState(prev => ({ ...prev, createdRelease: release, currentStep: 2 }));
    },
  });

  // Package creation mutation
  const createPackageMutation = useMutation({
    mutationFn: (data: PackageFormData) => packagesApi.create(data),
    onSuccess: (pkg) => {
      queryClient.invalidateQueries({ queryKey: ['packages'] });
      setState(prev => ({ ...prev, createdPackage: pkg, currentStep: 3 }));
    },
  });

  const goToStep = useCallback((step: number) => {
    setState(prev => ({ ...prev, currentStep: step }));
  }, []);

  const skipPackageStep = useCallback(() => {
    setState(prev => ({ ...prev, skipPackage: true, currentStep: 3 }));
  }, []);

  const reset = useCallback(() => {
    setState({
      currentStep: 0,
      createdStudy: null,
      createdRelease: null,
      createdPackage: null,
      skipPackage: false,
    });
    createStudyMutation.reset();
    createReleaseMutation.reset();
    createPackageMutation.reset();
  }, [createStudyMutation, createReleaseMutation, createPackageMutation]);

  return {
    ...state,
    createStudyMutation,
    createReleaseMutation,
    createPackageMutation,
    goToStep,
    skipPackageStep,
    reset,
    isLoading:
      createStudyMutation.isPending ||
      createReleaseMutation.isPending ||
      createPackageMutation.isPending,
  };
}
