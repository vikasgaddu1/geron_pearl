import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PriorityBadge } from '@/components/common/StatusBadge'
import { MessageSquare, User, Calendar } from 'lucide-react'
import type { ReportingEffortItemTracker, Priority } from '@/types'
import { formatDate } from '@/lib/utils'

interface KanbanCardProps {
  tracker: ReportingEffortItemTracker
  statusField: 'production' | 'qc'
  onClick?: () => void
}

export function KanbanCard({ tracker, statusField, onClick }: KanbanCardProps) {
  const programmer = statusField === 'production' 
    ? tracker.production_programmer 
    : tracker.qc_programmer
  
  const hasUnresolvedComments = (tracker.unresolved_comment_count || 0) > 0

  return (
    <Card 
      className="cursor-pointer hover:shadow-md transition-shadow bg-card border"
      onClick={onClick}
    >
      <CardContent className="p-3 space-y-2">
        {/* Item Code */}
        <div className="font-medium text-sm truncate" title={tracker.item_code}>
          {tracker.item_code}
        </div>
        
        {/* Item Type Badge */}
        <div className="flex gap-1 flex-wrap">
          {tracker.item_type && (
            <Badge variant="outline" className="text-xs">
              {tracker.item_type}
            </Badge>
          )}
          {tracker.item_subtype && (
            <Badge variant="secondary" className="text-xs">
              {tracker.item_subtype}
            </Badge>
          )}
        </div>
        
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
              {programmer?.username || 'Unassigned'}
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
        
        {/* In Production Flag */}
        {tracker.in_production_flag && (
          <Badge variant="success" className="text-xs">
            In Production
          </Badge>
        )}
      </CardContent>
    </Card>
  )
}

