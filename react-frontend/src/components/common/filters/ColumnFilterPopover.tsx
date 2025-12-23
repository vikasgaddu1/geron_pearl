import { ReactNode } from 'react'
import { Filter } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface ColumnFilterPopoverProps {
  children: ReactNode
  isActive?: boolean
  onClear?: () => void
  filterSummary?: string
  className?: string
}

export function ColumnFilterPopover({
  children,
  isActive = false,
  onClear,
  filterSummary,
  className,
}: ColumnFilterPopoverProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn(
            'h-7 w-7 p-0 hover:bg-accent',
            isActive && 'text-primary hover:text-primary',
            className
          )}
        >
          <Filter
            className={cn(
              'h-3.5 w-3.5',
              isActive && 'fill-primary'
            )}
          />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start">
        <div className="space-y-4">
          {/* Filter Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4" />
              <span className="font-semibold text-sm">Filter Column</span>
            </div>
            {isActive && (
              <Badge variant="secondary" className="text-xs">
                Active
              </Badge>
            )}
          </div>

          {/* Filter Component */}
          <div className="max-h-[400px] overflow-y-auto">
            {children}
          </div>

          {/* Filter Summary */}
          {isActive && filterSummary && (
            <div className="pt-2 border-t">
              <p className="text-xs text-muted-foreground">
                <span className="font-medium">Current filter:</span> {filterSummary}
              </p>
            </div>
          )}

          {/* Actions */}
          {isActive && onClear && (
            <div className="flex justify-end pt-2 border-t">
              <Button
                variant="outline"
                size="sm"
                onClick={onClear}
              >
                Reset Filter
              </Button>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}


