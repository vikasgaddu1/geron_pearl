/**
 * Step 1: Create Study form
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { BookOpen, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { studySchema, type StudyFormData } from '../schemas/quickStartSchemas';

interface StudyStepProps {
  onSubmit: (data: StudyFormData) => void;
  isLoading: boolean;
  error?: string;
}

export function StudyStep({ onSubmit, isLoading, error }: StudyStepProps) {
  const form = useForm<StudyFormData>({
    resolver: zodResolver(studySchema),
    defaultValues: {
      study_label: '',
      description: '',
    },
  });

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-12 h-12 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
          <BookOpen className="w-6 h-6 text-blue-600" />
        </div>
        <h3 className="text-lg font-medium">Create Your First Study</h3>
        <p className="text-sm text-gray-500 mt-1">
          A study represents a clinical trial or research project.
        </p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="study_label">Study Label *</Label>
          <Input
            id="study_label"
            placeholder="e.g., STUDY-001 or ABC-1234"
            {...form.register('study_label')}
          />
          {form.formState.errors.study_label && (
            <p className="text-sm text-red-500">
              {form.formState.errors.study_label.message}
            </p>
          )}
          <p className="text-xs text-gray-500">
            Use a unique identifier for your study (letters, numbers, hyphens, underscores)
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">Description (optional)</Label>
          <Textarea
            id="description"
            placeholder="Brief description of the study..."
            rows={3}
            {...form.register('description')}
          />
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
              Creating Study...
            </>
          ) : (
            'Create Study & Continue'
          )}
        </Button>
      </form>
    </div>
  );
}
