import { useMemo } from 'react'
import { BiostatKanbanColumn } from './BiostatKanbanColumn'
import type { ReportingEffortItemTracker, BiostatStatus, Priority } from '@/types'

interface BiostatKanbanBoardProps {
  trackers: ReportingEffortItemTracker[]
  onCardClick?: (tracker: ReportingEffortItemTracker) => void
  onBiostatStatusChange?: (trackerId: number, newStatus: BiostatStatus) => void
  onProductionFlagToggle?: (trackerId: number, newValue: boolean) => void
}

// Column configurations for biostat review
const BIOSTAT_COLUMNS: { status: BiostatStatus; title: string; colorClass: string }[] = [
  { status: 'pending', title: 'Pending Review', colorClass: 'bg-orange-200 text-orange-800' },
  { status: 'passed', title: 'Passed', colorClass: 'bg-green-200 text-green-800' },
]

// Priority order for sorting (lower number = higher priority)
const PRIORITY_ORDER: Record<Priority | 'none', number> = {
  critical: 1,
  high: 2,
  medium: 3,
  low: 4,
  none: 5,
}

// Get the highest priority value from a list of trackers
function getHighestPriority(trackers: ReportingEffortItemTracker[]): number {
  if (trackers.length === 0) return PRIORITY_ORDER.none
  return Math.min(...trackers.map(t => PRIORITY_ORDER[t.priority || 'none']))
}

export function BiostatKanbanBoard({
  trackers,
  onCardClick,
  onBiostatStatusChange,
  onProductionFlagToggle
}: BiostatKanbanBoardProps) {
  // Filter to only TLF items with pending or passed biostat status
  const tlfTrackers = useMemo(() => {
    return trackers.filter(t =>
      t.item_type === 'TLF' &&
      (t.biostat_status === 'pending' || t.biostat_status === 'passed')
    )
  }, [trackers])

  // Group trackers by item_subtype (Table, Listing, Figure) and sort swimlanes by highest priority
  const swimlanes = useMemo(() => {
    // Group trackers by item_subtype
    const subtypeGroups = new Map<string, ReportingEffortItemTracker[]>()

    tlfTrackers.forEach(tracker => {
      const subtype = tracker.item_subtype || 'Uncategorized'
      if (!subtypeGroups.has(subtype)) {
        subtypeGroups.set(subtype, [])
      }
      subtypeGroups.get(subtype)!.push(tracker)
    })

    // Convert to array and sort by highest priority in each group
    return Array.from(subtypeGroups.entries())
      .map(([subtype, subtypeTrackers]) => ({
        subtype,
        trackers: subtypeTrackers,
        highestPriority: getHighestPriority(subtypeTrackers),
      }))
      .sort((a, b) => a.highestPriority - b.highestPriority)
  }, [tlfTrackers])

  return (
    <div className="space-y-6">
      {swimlanes.map(swimlane => (
        <div key={swimlane.subtype} className="border rounded-lg overflow-hidden">
          {/* Swimlane Header */}
          <div className="bg-slate-100 dark:bg-slate-800 px-4 py-2 border-b">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200">
                {swimlane.subtype}
              </h3>
              <span className="text-xs text-muted-foreground">
                {swimlane.trackers.length} {swimlane.trackers.length === 1 ? 'item' : 'items'}
              </span>
            </div>
          </div>

          {/* Swimlane Columns */}
          <div className="flex gap-4 overflow-x-auto p-4 bg-slate-50/50 dark:bg-slate-900/30">
            {BIOSTAT_COLUMNS.map(column => (
              <BiostatKanbanColumn
                key={`${swimlane.subtype}-${column.status}`}
                title={column.title}
                status={column.status}
                trackers={swimlane.trackers}
                colorClass={column.colorClass}
                onCardClick={onCardClick}
                onBiostatStatusChange={onBiostatStatusChange}
                onProductionFlagToggle={onProductionFlagToggle}
              />
            ))}
          </div>
        </div>
      ))}

      {swimlanes.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <p className="mb-2">No TLF items pending biostat review</p>
          <p className="text-sm">TLF items appear here after QC marks them as completed</p>
        </div>
      )}
    </div>
  )
}
