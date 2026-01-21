import { useState, DragEvent, useMemo } from 'react'
import { cn } from '@/lib/utils'
import { BiostatKanbanCard } from './BiostatKanbanCard'
import { toast } from 'sonner'
import type { ReportingEffortItemTracker, BiostatStatus, Priority } from '@/types'

// Priority order for sorting (lower number = higher priority)
const PRIORITY_ORDER: Record<Priority | 'none', number> = {
  critical: 1,
  high: 2,
  medium: 3,
  low: 4,
  none: 5,
}

interface BiostatKanbanColumnProps {
  title: string
  status: BiostatStatus
  trackers: ReportingEffortItemTracker[]
  colorClass: string
  onCardClick?: (tracker: ReportingEffortItemTracker) => void
  onBiostatStatusChange?: (trackerId: number, newStatus: BiostatStatus) => void
  onProductionFlagToggle?: (trackerId: number, newValue: boolean) => void
}

export function BiostatKanbanColumn({
  title,
  status,
  trackers,
  colorClass,
  onCardClick,
  onBiostatStatusChange,
  onProductionFlagToggle
}: BiostatKanbanColumnProps) {
  const [isDragOver, setIsDragOver] = useState(false)

  // Filter and sort trackers by priority (highest priority on top)
  const filteredTrackers = useMemo(() => {
    return trackers
      .filter(t => t.biostat_status === status)
      .sort((a, b) => {
        const priorityA = PRIORITY_ORDER[a.priority || 'none']
        const priorityB = PRIORITY_ORDER[b.priority || 'none']
        return priorityA - priorityB
      })
  }, [trackers, status])

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setIsDragOver(true)
  }

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)

    const trackerId = e.dataTransfer.getData('trackerId')
    const draggedStatusField = e.dataTransfer.getData('statusField')
    const hasUnresolvedBiostatComments = e.dataTransfer.getData('hasUnresolvedBiostatComments') === 'true'

    // Only allow dropping if the status field matches (biostat)
    if (draggedStatusField !== 'biostat') {
      return
    }

    // Validation: Cannot pass if there are unresolved biostat comments
    if (status === 'passed' && hasUnresolvedBiostatComments) {
      toast.error('Cannot pass item: there are unresolved biostat comments')
      return
    }

    // Note: We don't allow dragging to 'failed' from the kanban - that requires a dialog with comment
    // Failed items are handled through the detail dialog, not drag-and-drop

    if (trackerId && onBiostatStatusChange) {
      onBiostatStatusChange(Number(trackerId), status)
    }
  }

  return (
    <div
      className={cn(
        "flex flex-col min-w-[280px] max-w-[320px] bg-muted/30 rounded-lg transition-all",
        isDragOver && "ring-2 ring-primary ring-offset-2"
      )}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
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
      <div className={cn(
        "flex-1 p-2 space-y-2 min-h-[200px] max-h-[calc(100vh-300px)] overflow-y-auto transition-colors",
        isDragOver && "bg-primary/5"
      )}>
        {filteredTrackers.length === 0 ? (
          <div className={cn(
            "text-center py-8 text-muted-foreground text-sm border-2 border-dashed rounded-lg",
            isDragOver ? "border-primary bg-primary/10" : "border-transparent"
          )}>
            {isDragOver ? "Drop here" : "No items"}
          </div>
        ) : (
          filteredTrackers.map(tracker => (
            <BiostatKanbanCard
              key={tracker.id}
              tracker={tracker}
              onClick={() => onCardClick?.(tracker)}
              isDraggable={status === 'pending'} // Only pending items can be dragged
              onProductionFlagToggle={onProductionFlagToggle}
            />
          ))
        )}
      </div>
    </div>
  )
}
