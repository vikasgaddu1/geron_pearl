/**
 * Velocity Trend Chart component
 * 
 * Shows weekly velocity (complexity points) over time using Recharts
 */

import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { WeeklyDataPoint } from '@/types/analytics'

interface VelocityTrendChartProps {
  data: WeeklyDataPoint[]
  title?: string
  avgPointsPerWeek: number
  isLoading?: boolean
}

export function VelocityTrendChart({ 
  data, 
  title = 'Weekly Velocity Trend',
  avgPointsPerWeek,
  isLoading = false
}: VelocityTrendChartProps) {
  // Format data for the chart
  const chartData = data
    .map((d) => ({
      week: `W${d.iso_week}`,
      fullLabel: `${d.iso_year}-W${d.iso_week}`,
      points: d.complexity_points,
      items: d.item_count,
    }))
    .reverse() // Show oldest to newest

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-gray-100 dark:bg-gray-800 animate-pulse rounded" />
        </CardContent>
      </Card>
    )
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-gray-500">
            No velocity data available yet
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">{title}</CardTitle>
          <div className="text-sm text-gray-500">
            Avg: <span className="font-semibold text-gray-700 dark:text-gray-300">{avgPointsPerWeek.toFixed(1)}</span> pts/week
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorPoints" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis 
                dataKey="week" 
                tick={{ fontSize: 12 }}
                tickLine={false}
                className="text-gray-500"
              />
              <YAxis 
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                className="text-gray-500"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                }}
                labelFormatter={(label, payload) => {
                  if (payload && payload[0]) {
                    return payload[0].payload.fullLabel
                  }
                  return label
                }}
                formatter={(value: number, name: string) => [
                  name === 'points' ? `${value} complexity points` : `${value} items`,
                  name === 'points' ? 'Velocity' : 'Items Completed'
                ]}
              />
              <Area
                type="monotone"
                dataKey="points"
                stroke="#6366f1"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorPoints)"
              />
              {/* Average line */}
              <Line
                type="monotone"
                dataKey={() => avgPointsPerWeek}
                stroke="#10b981"
                strokeDasharray="5 5"
                strokeWidth={1}
                dot={false}
                name="Average"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

