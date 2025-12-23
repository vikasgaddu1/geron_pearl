import { HelpCircle } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface HelpIconProps {
  title?: string
  content: string | React.ReactNode
  side?: 'top' | 'right' | 'bottom' | 'left'
  className?: string
}

export function HelpIcon({
  title,
  content,
  side = 'top',
  className,
}: HelpIconProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className={cn('h-5 w-5 p-0 hover:bg-accent', className)}
        >
          <HelpCircle className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors" />
        </Button>
      </PopoverTrigger>
      <PopoverContent side={side} className="w-80">
        <div className="space-y-2">
          {title && (
            <h4 className="font-semibold text-sm">{title}</h4>
          )}
          <div className="text-sm text-muted-foreground leading-relaxed">
            {typeof content === 'string' ? (
              <p>{content}</p>
            ) : (
              content
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}


