import { ReactNode } from 'react'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface TooltipWrapperProps {
  content: string
  side?: 'top' | 'right' | 'bottom' | 'left'
  children: ReactNode
  delayDuration?: number
}

export function TooltipWrapper({
  content,
  side = 'top',
  children,
  delayDuration = 300,
}: TooltipWrapperProps) {
  return (
    <TooltipProvider delayDuration={delayDuration}>
      <Tooltip>
        <TooltipTrigger asChild>
          {children}
        </TooltipTrigger>
        <TooltipContent side={side}>
          <p>{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}


