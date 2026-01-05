import { cn } from '@/lib/utils'
import { KanbanCard } from './KanbanCard'
import type { ReportingEffortItemTracker, ProductionStatus, QCStatus } from '@/types'

interface KanbanColumnProps {
  title: string
  status: ProductionStatus | QCStatus
  trackers: ReportingEffortItemTracker[]
  statusField: 'production' | 'qc'
  colorClass: string
  onCardClick?: (tracker: ReportingEffortItemTracker) => void
}

export function KanbanColumn({ 
  title, 
  status, 
  trackers, 
  statusField, 
  colorClass,
  onCardClick 
}: KanbanColumnProps) {
  const filteredTrackers = trackers.filter(t => 
    statusField === 'production' 
      ? t.production_status === status 
      : t.qc_status === status
  )

  return (
    <div className="flex flex-col min-w-[280px] max-w-[320px] bg-muted/30 rounded-lg">
      {/* Column Header */}
      <div className={cn(
        "flex items-center justify-between p-3 rounded-t-lg",
        colorClass
      )}>
        <h3 className="font-semibold text-sm">{title}</h3>
        <span className="bg-white/90 text-gray-800 text-xs font-medium px-2 py-0.5 rounded-full">
          {filteredTrackers.length}
        </span>
      </div>
      
      {/* Cards Container */}
      <div className="flex-1 p-2 space-y-2 min-h-[200px] max-h-[calc(100vh-300px)] overflow-y-auto">
        {filteredTrackers.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No items
          </div>
        ) : (
          filteredTrackers.map(tracker => (
            <KanbanCard
              key={tracker.id}
              tracker={tracker}
              statusField={statusField}
              onClick={() => onCardClick?.(tracker)}
            />
          ))
        )}
      </div>
    </div>
  )
}

