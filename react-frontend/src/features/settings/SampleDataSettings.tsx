/**
 * Sample Data Settings Component
 * 
 * Allows admins to manage sample data: seed, reset, or clear all data.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Database, 
  RefreshCw, 
  Trash2, 
  AlertTriangle, 
  CheckCircle2, 
  Loader2,
  Plus,
} from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  getSampleDataStatus,
  seedSampleData,
  resetToSampleData,
  clearAllData,
} from '@/api/endpoints/tenant-data';

export function SampleDataSettings() {
  const queryClient = useQueryClient();
  const [confirmAction, setConfirmAction] = useState<'reset' | 'clear' | null>(null);

  // Fetch sample data status
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['sampleDataStatus'],
    queryFn: getSampleDataStatus,
  });

  // Seed sample data
  const seedMutation = useMutation({
    mutationFn: seedSampleData,
    onSuccess: (data) => {
      toast.success(`Sample data seeded: ${data.counts.studies} studies, ${data.counts.packages} packages`);
      queryClient.invalidateQueries({ queryKey: ['sampleDataStatus'] });
      // Invalidate other queries that would be affected
      queryClient.invalidateQueries({ queryKey: ['studies'] });
      queryClient.invalidateQueries({ queryKey: ['packages'] });
      queryClient.invalidateQueries({ queryKey: ['textElements'] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to seed sample data');
    },
  });

  // Reset to sample data
  const resetMutation = useMutation({
    mutationFn: resetToSampleData,
    onSuccess: (data) => {
      toast.success(
        `Data reset complete: Cleared ${data.cleared.studies} studies, seeded ${data.seeded.studies} new studies`
      );
      queryClient.invalidateQueries({ queryKey: ['sampleDataStatus'] });
      queryClient.invalidateQueries({ queryKey: ['studies'] });
      queryClient.invalidateQueries({ queryKey: ['packages'] });
      queryClient.invalidateQueries({ queryKey: ['textElements'] });
      setConfirmAction(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to reset data');
      setConfirmAction(null);
    },
  });

  // Clear all data
  const clearMutation = useMutation({
    mutationFn: clearAllData,
    onSuccess: (data) => {
      toast.success(`All data cleared: ${data.studies} studies, ${data.packages} packages deleted`);
      queryClient.invalidateQueries({ queryKey: ['sampleDataStatus'] });
      queryClient.invalidateQueries({ queryKey: ['studies'] });
      queryClient.invalidateQueries({ queryKey: ['packages'] });
      queryClient.invalidateQueries({ queryKey: ['textElements'] });
      setConfirmAction(null);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to clear data');
      setConfirmAction(null);
    },
  });

  const isLoading = seedMutation.isPending || resetMutation.isPending || clearMutation.isPending;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Sample Data Management
            </CardTitle>
            <CardDescription>
              Manage demo data for testing and exploration
            </CardDescription>
          </div>
          {statusLoading ? (
            <Badge variant="secondary">Loading...</Badge>
          ) : status?.has_sample_data ? (
            <Badge variant="default" className="bg-green-500">
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Sample Data Active
            </Badge>
          ) : (
            <Badge variant="secondary">No Sample Data</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Sample data includes demo studies (DEMO-001, DEMO-002), packages (PKG-SAFETY, PKG-EFFICACY, 
          PKG-DEMOGRAPHICS), and text elements to help you explore PEARL's features.
        </p>

        <div className="flex flex-wrap gap-3">
          {/* Seed Sample Data - only show if no sample data exists */}
          {!status?.has_sample_data && (
            <Button
              variant="outline"
              onClick={() => seedMutation.mutate()}
              disabled={isLoading}
            >
              {seedMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              Seed Sample Data
            </Button>
          )}

          {/* Reset to Sample Data */}
          <AlertDialog open={confirmAction === 'reset'} onOpenChange={(open) => !open && setConfirmAction(null)}>
            <AlertDialogTrigger asChild>
              <Button
                variant="outline"
                onClick={() => setConfirmAction('reset')}
                disabled={isLoading}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Reset to Sample Data
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  Reset All Data?
                </AlertDialogTitle>
                <AlertDialogDescription className="space-y-2">
                  <p>
                    This will <strong>permanently delete all existing data</strong> (studies, 
                    packages, text elements, reporting efforts, trackers) and replace it with 
                    sample data.
                  </p>
                  <p className="text-destructive font-medium">
                    This action cannot be undone!
                  </p>
                  <p>User accounts will be preserved.</p>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => resetMutation.mutate()}
                  className="bg-yellow-500 hover:bg-yellow-600"
                >
                  {resetMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  Yes, Reset Data
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>

          {/* Clear All Data */}
          <AlertDialog open={confirmAction === 'clear'} onOpenChange={(open) => !open && setConfirmAction(null)}>
            <AlertDialogTrigger asChild>
              <Button
                variant="destructive"
                onClick={() => setConfirmAction('clear')}
                disabled={isLoading}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear All Data
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle className="flex items-center gap-2 text-destructive">
                  <AlertTriangle className="h-5 w-5" />
                  Delete All Data?
                </AlertDialogTitle>
                <AlertDialogDescription className="space-y-2">
                  <p>
                    This will <strong>permanently delete all data</strong> including:
                  </p>
                  <ul className="list-disc list-inside text-sm space-y-1 mt-2">
                    <li>All studies, database releases, and reporting efforts</li>
                    <li>All packages and package items</li>
                    <li>All text elements (titles, footnotes, etc.)</li>
                    <li>All tracker data and comments</li>
                  </ul>
                  <p className="text-destructive font-medium mt-3">
                    This action CANNOT be undone!
                  </p>
                  <p>User accounts will be preserved.</p>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => clearMutation.mutate()}
                  className="bg-destructive hover:bg-destructive/90"
                >
                  {clearMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4 mr-2" />
                  )}
                  Yes, Delete Everything
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </CardContent>
    </Card>
  );
}
