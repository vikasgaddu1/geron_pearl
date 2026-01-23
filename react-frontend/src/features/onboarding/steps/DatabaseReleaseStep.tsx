/**
 * Step 2: Create Database Release form
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Database, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { databaseReleaseSchema, type DatabaseReleaseFormData } from '../schemas/quickStartSchemas';
import type { Study } from '@/types';

interface DatabaseReleaseStepProps {
  study: Study;
  onSubmit: (data: DatabaseReleaseFormData & { study_id: number }) => void;
  isLoading: boolean;
  error?: string;
}

export function DatabaseReleaseStep({ study, onSubmit, isLoading, error }: DatabaseReleaseStepProps) {
  // Default to 30 days from now for the release date
  const defaultDate = new Date();
  defaultDate.setDate(defaultDate.getDate() + 30);
  const defaultDateStr = defaultDate.toISOString().split('T')[0];

  const form = useForm<DatabaseReleaseFormData>({
    resolver: zodResolver(databaseReleaseSchema),
    defaultValues: {
      database_release_label: '',
      database_release_date: defaultDateStr,
    },
  });

  const handleSubmit = (data: DatabaseReleaseFormData) => {
    onSubmit({ ...data, study_id: study.id });
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-12 h-12 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
          <Database className="w-6 h-6 text-green-600" />
        </div>
        <h3 className="text-lg font-medium">Add a Database Release</h3>
        <p className="text-sm text-gray-500 mt-1">
          Database releases represent data snapshots for <strong>{study.study_label}</strong>
        </p>
      </div>

      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="database_release_label">Release Label *</Label>
          <Input
            id="database_release_label"
            placeholder="e.g., DBR-001 or Interim-Analysis"
            {...form.register('database_release_label')}
          />
          {form.formState.errors.database_release_label && (
            <p className="text-sm text-red-500">
              {form.formState.errors.database_release_label.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="database_release_date">Release Date *</Label>
          <Input
            id="database_release_date"
            type="date"
            {...form.register('database_release_date')}
          />
          {form.formState.errors.database_release_date && (
            <p className="text-sm text-red-500">
              {form.formState.errors.database_release_date.message}
            </p>
          )}
          <p className="text-xs text-gray-500">
            The expected date for this data snapshot
          </p>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Creating Release...
            </>
          ) : (
            'Create Release & Continue'
          )}
        </Button>
      </form>
    </div>
  );
}
