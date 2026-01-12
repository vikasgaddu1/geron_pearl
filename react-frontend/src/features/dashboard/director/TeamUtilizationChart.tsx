/**
 * Team Utilization Chart component
 * 
 * Shows allocation breakdown for all team members
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { TeamMemberUtilization, AssignmentDetail } from '@/types/analytics'

interface TeamUtilizationChartProps {
  members: TeamMemberUtilization[]
  isLoading?: boolean
}

export function TeamUtilizationChart({ members, isLoading = false }: TeamUtilizationChartProps) {
  // Sort by allocation (highest first)
  const sortedMembers = [...members].sort(
    (a, b) => b.total_allocation_percentage - a.total_allocation_percentage
  )

  const chartData = sortedMembers.map((m) => ({
    name: m.username.split(' ')[0], // First name only for chart
    fullName: m.username,
    allocation: m.total_allocation_percentage,
    studyCount: m.study_count,
    status: m.status,
    assignments: m.assignments,
  }))

  const getBarColor = (status: string) => {
    switch (status) {
      case 'over_allocated':
        return '#ef4444' // red
      case 'under_utilized':
        return '#f59e0b' // amber
      default:
        return '#6366f1' // indigo
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Team Utilization</CardTitle>
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
          <CardTitle className="text-lg">Team Utilization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-gray-500">
            No team members assigned
          </div>
        </CardContent>
      </Card>
    )
  }

  const overAllocated = members.filter(m => m.status === 'over_allocated').length
  const underUtilized = members.filter(m => m.status === 'under_utilized').length

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">Team Utilization</CardTitle>
          <div className="flex gap-2">
            {overAllocated > 0 && (
              <Badge variant="destructive">{overAllocated} over-allocated</Badge>
            )}
            {underUtilized > 0 && (
              <Badge className="bg-amber-500">{underUtilized} under-utilized</Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 50, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
              <XAxis
                type="number"
                domain={[0, 150]}
                tick={{ fontSize: 12 }}
                tickFormatter={(v) => `${v}%`}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 12 }}
                width={60}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                }}
                formatter={(value: number, name: string, entry) => {
                  const payload = entry.payload
                  return [
                    <div key="content" className="space-y-1">
                      <div className="font-medium">{payload.fullName}</div>
                      <div>Total: {value}%</div>
                      <div className="text-xs text-gray-500">
                        {payload.studyCount} studies
                      </div>
                      <div className="text-xs mt-1">
                        {payload.assignments.map((a: AssignmentDetail, i: number) => (
                          <div key={i}>
                            {a.study_label}: {a.allocation_percentage}%
                          </div>
                        ))}
                      </div>
                    </div>,
                    ''
                  ]
                }}
              />
              <ReferenceLine x={100} stroke="#10b981" strokeDasharray="5 5" label={{ value: '100%', position: 'top' }} />
              <Bar dataKey="allocation" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry.status)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-4 flex gap-4 justify-center text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-indigo-500" />
            <span className="text-gray-600 dark:text-gray-400">Healthy (50-100%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-red-500" />
            <span className="text-gray-600 dark:text-gray-400">Over-allocated (&gt;100%)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-amber-500" />
            <span className="text-gray-600 dark:text-gray-400">Under-utilized (&lt;50%)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

