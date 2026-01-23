/**
 * Step 3: Create Package form (optional)
 */

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Package, Loader2, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { packageSchema, type PackageFormData } from '../schemas/quickStartSchemas';

interface PackageStepProps {
  onSubmit: (data: PackageFormData) => void;
  onSkip: () => void;
  isLoading: boolean;
  error?: string;
}

export function PackageStep({ onSubmit, onSkip, isLoading, error }: PackageStepProps) {
  const form = useForm<PackageFormData>({
    resolver: zodResolver(packageSchema),
    defaultValues: {
      package_name: '',
      study_indication: '',
      therapeutic_area: '',
    },
  });

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-12 h-12 mx-auto mb-4 bg-purple-100 rounded-full flex items-center justify-center">
          <Package className="w-6 h-6 text-purple-600" />
        </div>
        <h3 className="text-lg font-medium">Create a Package (Optional)</h3>
        <p className="text-sm text-gray-500 mt-1">
          Packages organize your Tables, Figures, Listings, and Datasets.
        </p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="package_name">Package Name *</Label>
          <Input
            id="package_name"
            placeholder="e.g., PKG-SAFETY or CSR-Tables"
            {...form.register('package_name')}
          />
          {form.formState.errors.package_name && (
            <p className="text-sm text-red-500">
              {form.formState.errors.package_name.message}
            </p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="study_indication">Study Indication</Label>
          <Input
            id="study_indication"
            placeholder="e.g., Type 2 Diabetes"
            {...form.register('study_indication')}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="therapeutic_area">Therapeutic Area</Label>
          <Input
            id="therapeutic_area"
            placeholder="e.g., Oncology, Cardiology"
            {...form.register('therapeutic_area')}
          />
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        <div className="flex gap-3">
          <Button
            type="button"
            variant="outline"
            className="flex-1"
            onClick={onSkip}
            disabled={isLoading}
          >
            <SkipForward className="h-4 w-4 mr-2" />
            Skip for Now
          </Button>
          <Button type="submit" className="flex-1" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              'Create Package'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
