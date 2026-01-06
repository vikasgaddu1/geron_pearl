import { KanbanColumn } from './KanbanColumn'
import type { ReportingEffortItemTracker, ProductionStatus, QCStatus } from '@/types'

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

export function KanbanBoard({ trackers, statusField, onCardClick, onStatusChange, onProductionFlagToggle }: KanbanBoardProps) {
  const columns = statusField === 'production' ? PRODUCTION_COLUMNS : QC_COLUMNS

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {columns.map(column => (
        <KanbanColumn
          key={column.status}
          title={column.title}
          status={column.status}
          trackers={trackers}
          statusField={statusField}
          colorClass={column.colorClass}
          onCardClick={onCardClick}
          onStatusChange={onStatusChange}
          onProductionFlagToggle={onProductionFlagToggle}
        />
      ))}
    </div>
  )
}
