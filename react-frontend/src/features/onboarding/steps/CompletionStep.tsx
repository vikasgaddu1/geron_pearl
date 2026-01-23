/**
 * Step 4: Completion summary
 */

import { Check, BookOpen, Database, Package as PackageIcon, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { Study, DatabaseRelease, Package } from '@/types';

interface CompletionStepProps {
  study: Study;
  release: DatabaseRelease;
  pkg: Package | null;
  onComplete: () => void;
  onGoToStudyManagement: () => void;
}

export function CompletionStep({
  study,
  release,
  pkg,
  onComplete,
  onGoToStudyManagement,
}: CompletionStepProps) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
          <Check className="w-8 h-8 text-green-600" />
        </div>
        <h3 className="text-xl font-semibold">You're All Set!</h3>
        <p className="text-sm text-gray-500 mt-2">
          Your workspace is ready. Here's what you created:
        </p>
      </div>

      <div className="space-y-3 bg-gray-50 rounded-lg p-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <BookOpen className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <p className="text-sm font-medium">Study</p>
            <p className="text-sm text-gray-600">{study.study_label}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
            <Database className="w-4 h-4 text-green-600" />
          </div>
          <div>
            <p className="text-sm font-medium">Database Release</p>
            <p className="text-sm text-gray-600">{release.database_release_label}</p>
          </div>
        </div>

        {pkg && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
              <PackageIcon className="w-4 h-4 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-medium">Package</p>
              <p className="text-sm text-gray-600">{pkg.package_name}</p>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-3 text-sm text-gray-600">
        <p><strong>Next steps:</strong></p>
        <ul className="list-disc list-inside space-y-1 text-gray-500">
          <li>Add Reporting Efforts to track deliverables</li>
          <li>Create TLF items and assign programmers</li>
          <li>Invite team members to collaborate</li>
        </ul>
      </div>

      <div className="flex flex-col gap-2">
        <Button onClick={onGoToStudyManagement} className="w-full">
          <ArrowRight className="h-4 w-4 mr-2" />
          Go to Study Management
        </Button>
        <Button variant="outline" onClick={onComplete} className="w-full">
          Go to Dashboard
        </Button>
      </div>
    </div>
  );
}
