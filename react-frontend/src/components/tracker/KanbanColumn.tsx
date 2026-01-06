import { useState, DragEvent } from 'react'
import { cn } from '@/lib/utils'
import { KanbanCard } from './KanbanCard'
import { toast } from 'sonner'
import type { ReportingEffortItemTracker, ProductionStatus, QCStatus } from '@/types'

interface KanbanColumnProps {
  title: string
  status: ProductionStatus | QCStatus
  trackers: ReportingEffortItemTracker[]
  statusField: 'production' | 'qc'
  colorClass: string
  onCardClick?: (tracker: ReportingEffortItemTracker) => void
  onStatusChange?: (trackerId: number, newStatus: ProductionStatus | QCStatus) => void
  onProductionFlagToggle?: (trackerId: number, newValue: boolean) => void
}

export function KanbanColumn({ 
  title, 
  status, 
  trackers, 
  statusField, 
  colorClass,
  onCardClick,
  onStatusChange,
  onProductionFlagToggle
}: KanbanColumnProps) {
  const [isDragOver, setIsDragOver] = useState(false)

  const filteredTrackers = trackers.filter(t => 
    statusField === 'production' 
      ? t.production_status === status 
      : t.qc_status === status
  )

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
    const sourceProductionStatus = e.dataTransfer.getData('sourceProductionStatus')

    // Only allow dropping if the status field matches
    if (draggedStatusField !== statusField) {
      return
    }

    // Workflow validation for Production Kanban
    if (statusField === 'production') {
      // Cannot drag directly to 'completed' - it's auto-set by QC completion
      if (status === 'completed') {
        toast.error("Production status cannot be set to 'Completed' directly. It is automatically set when QC marks the item as completed.")
        return
      }
    }

    // Workflow validation for QC Kanban
    if (statusField === 'qc') {
      // Can only move to 'completed' or 'failed' when production is 'ready_for_qc'
      if ((status === 'completed' || status === 'failed') && sourceProductionStatus !== 'ready_for_qc') {
        toast.error(`QC can only be marked as '${status === 'completed' ? 'Completed' : 'Failed'}' when production status is 'Ready for QC'`)
        return
      }
    }

    if (trackerId && onStatusChange) {
      onStatusChange(Number(trackerId), status)
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
            <KanbanCard
              key={tracker.id}
              tracker={tracker}
              statusField={statusField}
              onClick={() => onCardClick?.(tracker)}
              isDraggable={true}
              onProductionFlagToggle={onProductionFlagToggle}
            />
          ))
        )}
      </div>
    </div>
  )
}
