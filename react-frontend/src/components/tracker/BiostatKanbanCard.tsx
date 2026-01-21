import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PriorityBadge } from '@/components/common/StatusBadge'
import { MessageSquare, User, Calendar, GripVertical, Factory, CheckCircle, AlertTriangle } from 'lucide-react'
import type { ReportingEffortItemTracker, Priority } from '@/types'
import { formatDate } from '@/lib/utils'
import { DragEvent } from 'react'

// Extended tracker type to handle flat API response fields
interface TrackerWithFlatFields extends ReportingEffortItemTracker {
  biostat_reviewer_username?: string
}

interface BiostatKanbanCardProps {
  tracker: ReportingEffortItemTracker
  onClick?: () => void
  isDraggable?: boolean
  onProductionFlagToggle?: (trackerId: number, newValue: boolean) => void
}

export function BiostatKanbanCard({ tracker, onClick, isDraggable = true, onProductionFlagToggle }: BiostatKanbanCardProps) {
  // Get biostat reviewer name
  const trackerData = tracker as TrackerWithFlatFields
  const reviewerName = tracker.biostat_reviewer?.username || trackerData.biostat_reviewer_username

  const hasUnresolvedBiostatComments = (tracker.unresolved_biostat_comment_count || 0) > 0
  const hasUnresolvedComments = (tracker.unresolved_comment_count || 0) > 0

  const handleDragStart = (e: DragEvent<HTMLDivElement>) => {
    // Store the tracker ID and status field in the drag data
    e.dataTransfer.setData('trackerId', String(tracker.id))
    e.dataTransfer.setData('statusField', 'biostat')
    e.dataTransfer.setData('hasUnresolvedBiostatComments', String(hasUnresolvedBiostatComments))
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
          {/* Biostat Status Badge */}
          {tracker.biostat_status === 'passed' && (
            <CheckCircle className="h-4 w-4 text-green-500" />
          )}
        </div>

        {/* Item Subtype Badge */}
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

        {/* Bottom Row - Reviewer and Due Date */}
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-1 border-t">
          {/* Biostat Reviewer */}
          <div className="flex items-center gap-1">
            <User className="h-3 w-3" />
            <span className="truncate max-w-[80px]">
              {reviewerName || 'Unassigned'}
            </span>
          </div>

          {/* Review Date */}
          {tracker.biostat_review_date && (
            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>{formatDate(tracker.biostat_review_date)}</span>
            </div>
          )}

          {/* Biostat Comments Badge */}
          {hasUnresolvedBiostatComments && (
            <div className="flex items-center gap-1 text-orange-500" title="Unresolved biostat comments">
              <AlertTriangle className="h-3 w-3" />
              <span>{tracker.unresolved_biostat_comment_count}</span>
            </div>
          )}

          {/* Regular Comments Badge */}
          {hasUnresolvedComments && !hasUnresolvedBiostatComments && (
            <div className="flex items-center gap-1 text-blue-500" title="Unresolved comments">
              <MessageSquare className="h-3 w-3" />
              <span>{tracker.unresolved_comment_count}</span>
            </div>
          )}
        </div>

        {/* In Production Flag - Only for passed items */}
        {tracker.biostat_status === 'passed' && (
          <div
            className="flex items-center gap-1 cursor-pointer hover:opacity-80"
            onClick={(e) => {
              e.stopPropagation() // Prevent card click
              if (onProductionFlagToggle) {
                onProductionFlagToggle(tracker.id, !tracker.in_production_flag)
              }
            }}
            title={tracker.in_production_flag ? 'Click to remove from production' : 'Click to mark as in production'}
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
        )}
      </CardContent>
    </Card>
  )
}
