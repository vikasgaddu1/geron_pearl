/**
 * Warning Banner component for Director Dashboard
 * 
 * Displays critical warnings that require attention:
 * - Items assigned to inactive team members
 * - Users over 100% allocation
 * - Capacity gaps
 */

import { AlertTriangle, UserX, Users, XCircle } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import type { DashboardWarnings } from '@/types/analytics'

interface WarningBannerProps {
  warnings: DashboardWarnings | null
  isLoading: boolean
}

export function WarningBanner({ warnings, isLoading }: WarningBannerProps) {
  if (isLoading) {
    return (
      <div className="h-24 bg-gray-100 dark:bg-gray-800 animate-pulse rounded-lg" />
    )
  }

  if (!warnings?.has_warnings) {
    return (
      <Alert className="border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950">
        <AlertTitle className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300">
          <span className="text-xl">✓</span> All Clear
        </AlertTitle>
        <AlertDescription className="text-emerald-600 dark:text-emerald-400">
          No critical warnings at this time. Team allocations are balanced and all items are assigned to active members.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-3">
      <Alert variant="destructive" className="border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-950">
        <AlertTriangle className="h-5 w-5 text-amber-600" />
        <AlertTitle className="text-amber-800 dark:text-amber-200 font-semibold">
          ⚠️ Attention Required
        </AlertTitle>
        <AlertDescription>
          <ul className="mt-2 space-y-2">
            {/* Orphaned items warning */}
            {warnings.orphaned_items.map((item) => (
              <li key={`orphan-${item.user_id}-${item.study_id}`} className="flex items-start gap-2 text-amber-700 dark:text-amber-300">
                <UserX className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>
                  <strong>{item.orphaned_item_count}</strong> items assigned to{' '}
                  <strong>{item.username}</strong>{' '}
                  {item.departure_reason && (
                    <span className="text-amber-600 dark:text-amber-400">
                      ({item.departure_reason.replace('_', ' ')})
                    </span>
                  )}{' '}
                  need reassignment on <strong>{item.study_label}</strong>
                </span>
              </li>
            ))}

            {/* Over-allocated users warning */}
            {warnings.over_allocated_users.map((user) => (
              <li key={`over-${user.user_id}`} className="flex items-start gap-2 text-amber-700 dark:text-amber-300">
                <Users className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>
                  <strong>{user.username}</strong> is allocated{' '}
                  <strong>{user.total_allocation}%</strong> across studies (exceeds 100%)
                </span>
              </li>
            ))}
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  )
}

