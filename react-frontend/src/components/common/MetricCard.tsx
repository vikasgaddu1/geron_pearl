import React from 'react'
import { Card, CardContent } from '@/components/ui/card'

export interface MetricCardProps {
  title: string
  value: number | string
  icon: React.ElementType
  variant?: 'default' | 'info' | 'warning' | 'danger' | 'success'
  className?: string
}

const colorClasses = {
  default: 'text-primary',
  info: 'text-blue-500',
  warning: 'text-yellow-500',
  danger: 'text-red-500',
  success: 'text-green-500',
} as const

/**
 * MetricCard - Displays a metric with an icon and value
 * Memoized to prevent unnecessary re-renders when used in grids
 */
export const MetricCard = React.memo(function MetricCard({
  title,
  value,
  icon: Icon,
  variant = 'default',
  className,
}: MetricCardProps) {
  return (
    <Card className={className}>
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <Icon className={`h-8 w-8 ${colorClasses[variant]}`} />
          <div>
            <p className={`text-3xl font-bold ${colorClasses[variant]}`}>{value}</p>
            <p className="text-sm text-muted-foreground">{title}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
})
