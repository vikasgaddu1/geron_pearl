import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PriorityBadge } from '@/components/common/StatusBadge'
import { MessageSquare, User, Calendar, GripVertical, Factory } from 'lucide-react'
import type { ReportingEffortItemTracker, Priority } from '@/types'
import { formatDate } from '@/lib/utils'
import { DragEvent } from 'react'

interface KanbanCardProps {
  tracker: ReportingEffortItemTracker
  statusField: 'production' | 'qc'
  onClick?: () => void
  isDraggable?: boolean
  onProductionFlagToggle?: (trackerId: number, newValue: boolean) => void
}

export function KanbanCard({ tracker, statusField, onClick, isDraggable = true, onProductionFlagToggle }: KanbanCardProps) {
  // Get programmer name - handle both nested object and flat username field formats
  // API returns flat fields: prod_programmer_username, qc_programmer_username
  // Types define nested objects: production_programmer?.username
  const trackerAny = tracker as any
  const programmerName = statusField === 'production' 
    ? (tracker.production_programmer?.username || trackerAny.prod_programmer_username)
    : (tracker.qc_programmer?.username || trackerAny.qc_programmer_username)
  
  const hasUnresolvedComments = (tracker.unresolved_comment_count || 0) > 0

  const handleDragStart = (e: DragEvent<HTMLDivElement>) => {
    // Store the tracker ID and current status in the drag data
    e.dataTransfer.setData('trackerId', String(tracker.id))
    e.dataTransfer.setData('statusField', statusField)
    // Include production status for QC workflow validation
    e.dataTransfer.setData('sourceProductionStatus', tracker.production_status || '')
    e.dataTransfer.effectAllowed = 'move'
    
    // Add visual feedback
    const target = e.target as HTMLElement
    target.classList.add('opacity-50')
  }

  const handleDragEnd = (e: DragEvent<HTMLDivElement>) => {
    // Remove visual feedback
    const target = e.target as HTMLElement
    target.classList.remove('opacity-50')
  }

  return (
    <Card 
      className="cursor-grab hover:shadow-md transition-shadow bg-card border active:cursor-grabbing"
      onClick={onClick}
      draggable={isDraggable}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <CardContent className="p-3 space-y-2">
        {/* Drag Handle and Item Code */}
        <div className="flex items-center gap-1">
          {isDraggable && (
            <GripVertical className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          )}
          <div className="font-medium text-sm truncate flex-1" title={tracker.item_code}>
            {tracker.item_code}
          </div>
        </div>
        
        {/* Item Subtype Badge (type is shown in swimlane header) */}
        {tracker.item_subtype && (
          <div className="flex gap-1 flex-wrap">
            <Badge variant="secondary" className="text-xs">
              {tracker.item_subtype}
            </Badge>
          </div>
        )}
        
        {/* Priority */}
        {tracker.priority && (
          <PriorityBadge priority={tracker.priority as Priority} />
        )}
        
        {/* Bottom Row - Programmer and Due Date */}
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-1 border-t">
          {/* Programmer */}
          <div className="flex items-center gap-1">
            <User className="h-3 w-3" />
            <span className="truncate max-w-[80px]">
              {programmerName || 'Unassigned'}
            </span>
          </div>
          
          {/* Due Date */}
          {tracker.due_date && (
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>{formatDate(tracker.due_date)}</span>
            </div>
          )}
          
          {/* Comments Badge */}
          {hasUnresolvedComments && (
            <div className="flex items-center gap-1 text-orange-500">
              <MessageSquare className="h-3 w-3" />
              <span>{tracker.unresolved_comment_count}</span>
            </div>
          )}
        </div>
        
        {/* In Production Flag - Always visible, clickable to toggle */}
        {(() => {
          // Cast to any to access flat fields from API response
          const trackerData = tracker as any
          const prodStatus = tracker.production_status || trackerData.production_status
          const qcStatus = tracker.qc_status || trackerData.qc_status
          const canToggle = prodStatus === 'completed' && qcStatus === 'completed'
          
          return (
            <div 
              className={`flex items-center gap-1 ${canToggle ? 'cursor-pointer hover:opacity-80' : 'cursor-not-allowed opacity-60'}`}
              onClick={(e) => {
                e.stopPropagation() // Prevent card click
                if (canToggle && onProductionFlagToggle) {
                  onProductionFlagToggle(tracker.id, !tracker.in_production_flag)
                }
              }}
              title={canToggle 
                ? (tracker.in_production_flag ? 'Click to remove from production' : 'Click to mark as in production')
                : 'Both Production and QC must be Completed to toggle'}
            >
              {tracker.in_production_flag ? (
                <Badge variant="default" className="text-xs bg-emerald-600 hover:bg-emerald-700">
                  <Factory className="h-3 w-3 mr-1" />
                  In Production
                </Badge>
              ) : (
                <Badge variant="outline" className="text-xs text-muted-foreground">
                  <Factory className="h-3 w-3 mr-1" />
                  Not In Production
                </Badge>
              )}
            </div>
          )
        })()}
      </CardContent>
    </Card>
  )
}
