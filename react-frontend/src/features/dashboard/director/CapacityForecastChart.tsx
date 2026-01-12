/**
 * Capacity Forecast Chart component
 * 
 * Shows projected team capacity for upcoming weeks
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { ForecastWeek } from '@/types/analytics'

interface CapacityForecastChartProps {
  weeks: ForecastWeek[]
  isLoading?: boolean
}

export function CapacityForecastChart({ weeks, isLoading = false }: CapacityForecastChartProps) {
  const chartData = weeks.map((w) => ({
    week: `Week ${w.week_number}`,
    date: new Date(w.week_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    fte: w.fte,
    allocation: w.total_allocation_percentage,
  }))

  // Calculate average FTE
  const avgFte = chartData.reduce((sum, w) => sum + w.fte, 0) / chartData.length

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Capacity Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 bg-gray-100 dark:bg-gray-800 animate-pulse rounded" />
        </CardContent>
      </Card>
    )
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Capacity Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-gray-500">
            No forecast data available
          </div>
        </CardContent>
      </Card>
    )
  }

  // Find weeks with significant drops
  const drops = chartData.filter((w, i) => {
    if (i === 0) return false
    return chartData[i - 1].fte - w.fte > 0.5
  })

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">Capacity Forecast</CardTitle>
          <div className="text-sm text-gray-500">
            Avg: <span className="font-semibold text-gray-700 dark:text-gray-300">{avgFte.toFixed(1)}</span> FTE
          </div>
        </div>
        {drops.length > 0 && (
          <p className="text-xs text-amber-600 dark:text-amber-400">
            ⚠️ {drops.length} capacity drop{drops.length > 1 ? 's' : ''} detected
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 5, right: 20, left: -10, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 11 }}
                tickLine={false}
              />
              <YAxis 
                tick={{ fontSize: 11 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `${v}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                }}
                formatter={(value: number, name: string) => [
                  name === 'fte' ? `${value.toFixed(2)} FTE` : `${value}%`,
                  name === 'fte' ? 'Capacity' : 'Allocation'
                ]}
              />
              <ReferenceLine y={avgFte} stroke="#10b981" strokeDasharray="5 5" />
              <Line
                type="monotone"
                dataKey="fte"
                stroke="#6366f1"
                strokeWidth={2}
                dot={{ fill: '#6366f1', strokeWidth: 2 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

