import { useMemo } from 'react'
import { KanbanColumn } from './KanbanColumn'
import type { ReportingEffortItemTracker, ProductionStatus, QCStatus, Priority } from '@/types'

interface KanbanBoardProps {
  trackers: ReportingEffortItemTracker[]
  statusField: 'production' | 'qc'
  onCardClick?: (tracker: ReportingEffortItemTracker) => void
  onStatusChange?: (trackerId: number, newStatus: ProductionStatus | QCStatus) => void
  onProductionFlagToggle?: (trackerId: number, newValue: boolean) => void
}

// Column configurations for each status field
const PRODUCTION_COLUMNS: { status: ProductionStatus; title: string; colorClass: string }[] = [
  { status: 'not_started', title: 'Not Started', colorClass: 'bg-gray-200 text-gray-800' },
  { status: 'in_progress', title: 'In Progress', colorClass: 'bg-blue-200 text-blue-800' },
  { status: 'ready_for_qc', title: 'Ready for QC', colorClass: 'bg-purple-200 text-purple-800' },
  { status: 'completed', title: 'Completed', colorClass: 'bg-green-200 text-green-800' },
  { status: 'on_hold', title: 'On Hold', colorClass: 'bg-yellow-200 text-yellow-800' },
]

const QC_COLUMNS: { status: QCStatus; title: string; colorClass: string }[] = [
  { status: 'not_started', title: 'Not Started', colorClass: 'bg-gray-200 text-gray-800' },
  { status: 'in_progress', title: 'In Progress', colorClass: 'bg-blue-200 text-blue-800' },
  { status: 'failed', title: 'Failed', colorClass: 'bg-red-200 text-red-800' },
  { status: 'completed', title: 'Completed', colorClass: 'bg-green-200 text-green-800' },
  { status: 'on_hold', title: 'On Hold', colorClass: 'bg-yellow-200 text-yellow-800' },
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

export function KanbanBoard({ trackers, statusField, onCardClick, onStatusChange, onProductionFlagToggle }: KanbanBoardProps) {
  const columns = statusField === 'production' ? PRODUCTION_COLUMNS : QC_COLUMNS

  // Group trackers by item_type and sort swimlanes by highest priority
  const swimlanes = useMemo(() => {
    // Group trackers by item_type
    const typeGroups = new Map<string, ReportingEffortItemTracker[]>()
    
    trackers.forEach(tracker => {
      const type = tracker.item_type || 'Uncategorized'
      if (!typeGroups.has(type)) {
        typeGroups.set(type, [])
      }
      typeGroups.get(type)!.push(tracker)
    })

    // Convert to array and sort by highest priority in each group
    return Array.from(typeGroups.entries())
      .map(([type, typeTrackers]) => ({
        type,
        trackers: typeTrackers,
        highestPriority: getHighestPriority(typeTrackers),
      }))
      .sort((a, b) => a.highestPriority - b.highestPriority)
  }, [trackers])

  return (
    <div className="space-y-6">
      {swimlanes.map(swimlane => (
        <div key={swimlane.type} className="border rounded-lg overflow-hidden">
          {/* Swimlane Header */}
          <div className="bg-slate-100 dark:bg-slate-800 px-4 py-2 border-b">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-sm text-slate-700 dark:text-slate-200">
                {swimlane.type}
              </h3>
              <span className="text-xs text-muted-foreground">
                {swimlane.trackers.length} {swimlane.trackers.length === 1 ? 'item' : 'items'}
              </span>
            </div>
          </div>
          
          {/* Swimlane Columns */}
          <div className="flex gap-4 overflow-x-auto p-4 bg-slate-50/50 dark:bg-slate-900/30">
            {columns.map(column => (
              <KanbanColumn
                key={`${swimlane.type}-${column.status}`}
                title={column.title}
                status={column.status}
                trackers={swimlane.trackers}
                statusField={statusField}
                colorClass={column.colorClass}
                onCardClick={onCardClick}
                onStatusChange={onStatusChange}
                onProductionFlagToggle={onProductionFlagToggle}
              />
            ))}
          </div>
        </div>
      ))}
      
      {swimlanes.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No items to display
        </div>
      )}
    </div>
  )
}
