import { useMemo } from 'react'
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Cell,
  CartesianGrid,
} from 'recharts'
import { format, parseISO, differenceInDays, startOfDay, addDays, min, max } from 'date-fns'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, Clock, AlertTriangle, Calendar } from 'lucide-react'
import type { ReportingEffortMilestoneWithContext } from '@/types'

interface MilestoneGanttProps {
  milestones: ReportingEffortMilestoneWithContext[]
  title?: string
  showLegend?: boolean
  height?: number
  className?: string
}

interface GanttDataPoint {
  id: number
  name: string
  phaseName: string
  startDate: Date | null
  dueDate: Date | null
  startOffset: number  // Days from chart start to milestone start
  duration: number     // Duration in days (width of bar)
  responsibility: string
  isCompleted: boolean
  isOverdue: boolean
  studyLabel: string
  reportingEffortLabel: string
  comments?: string
}

// Color palette for phases - distinctive and colorblind-friendly
const PHASE_COLORS = [
  '#3b82f6', // blue
  '#10b981', // emerald
  '#f59e0b', // amber
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
  '#84cc16', // lime
]

const STATUS_COLORS = {
  completed: '#22c55e',
  overdue: '#ef4444',
  upcoming: '#3b82f6',
  today: '#f59e0b',
}

export function MilestoneGantt({
  milestones,
  title = 'Project Timeline',
  showLegend = true,
  height = 400,
  className,
}: MilestoneGanttProps) {
  const today = startOfDay(new Date())

  // Process milestones into chart data
  const { chartData, dateRange, phaseColorMap } = useMemo(() => {
    if (!milestones.length) {
      return { chartData: [], dateRange: { min: today, max: addDays(today, 30) }, phaseColorMap: new Map() }
    }

    // Parse dates - include both start_date and due_date
    const milestonesWithDates = milestones
      .filter(m => m.start_date || m.due_date)  // At least one date required
      .map(m => ({
        ...m,
        parsedStartDate: m.start_date ? startOfDay(parseISO(m.start_date)) : null,
        parsedDueDate: m.due_date ? startOfDay(parseISO(m.due_date)) : null,
      }))
      .sort((a, b) => {
        // Sort by earliest date (start or due)
        const aDate = a.parsedStartDate || a.parsedDueDate
        const bDate = b.parsedStartDate || b.parsedDueDate
        return (aDate?.getTime() || 0) - (bDate?.getTime() || 0)
      })

    if (!milestonesWithDates.length) {
      return { chartData: [], dateRange: { min: today, max: addDays(today, 30) }, phaseColorMap: new Map() }
    }

    // Calculate date range including all start and due dates
    const allDates = milestonesWithDates.flatMap(m => [m.parsedStartDate, m.parsedDueDate].filter(Boolean) as Date[])
    const minDate = min(allDates)
    const maxDate = max(allDates)

    // Add padding to date range
    const paddedMin = addDays(minDate, -3)
    const paddedMax = addDays(maxDate, 3)

    // Create phase color mapping
    const uniquePhases = [...new Set(milestonesWithDates.map(m => m.phase_name || 'Unknown'))]
    const colorMap = new Map<string, string>()
    uniquePhases.forEach((phase, idx) => {
      colorMap.set(phase, PHASE_COLORS[idx % PHASE_COLORS.length])
    })

    // Create chart data points with duration bars
    const data: GanttDataPoint[] = milestonesWithDates.map((m) => {
      // Determine effective start and end dates
      const effectiveStart = m.parsedStartDate || m.parsedDueDate!
      const effectiveEnd = m.parsedDueDate || m.parsedStartDate!

      // Calculate offset from chart start to milestone start
      const startOffset = differenceInDays(effectiveStart, paddedMin)

      // Calculate duration (minimum 1 day for visibility)
      const duration = Math.max(1, differenceInDays(effectiveEnd, effectiveStart) + 1)

      const isOverdue = !m.is_completed && effectiveEnd < today

      return {
        id: m.id,
        name: m.name,
        phaseName: m.phase_name || 'Unknown',
        startDate: m.parsedStartDate,
        dueDate: m.parsedDueDate,
        startOffset,
        duration,
        responsibility: m.responsibility || 'Unassigned',
        isCompleted: m.is_completed,
        isOverdue,
        studyLabel: m.study_label || '',
        reportingEffortLabel: m.reporting_effort_label || '',
        comments: m.comments,
      }
    })

    return {
      chartData: data,
      dateRange: { min: paddedMin, max: paddedMax },
      phaseColorMap: colorMap,
    }
  }, [milestones, today])

  // Calculate total days for x-axis
  const totalDays = useMemo(() => {
    return differenceInDays(dateRange.max, dateRange.min) + 1
  }, [dateRange])

  // Today's position on the chart
  const todayOffset = useMemo(() => {
    const offset = differenceInDays(today, dateRange.min)
    return offset >= 0 && offset <= totalDays ? offset : null
  }, [today, dateRange, totalDays])

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: GanttDataPoint }> }) => {
    if (!active || !payload?.length) return null

    const data = payload[0].payload
    return (
      <div className="bg-popover border rounded-lg shadow-lg p-3 max-w-xs">
        <div className="font-semibold text-sm mb-1">{data.name}</div>
        <div className="text-xs text-muted-foreground space-y-1">
          {data.startDate && data.dueDate ? (
            <div className="flex items-center gap-2">
              <Calendar className="h-3 w-3" />
              <span>
                {format(data.startDate, 'MMM d')} → {format(data.dueDate, 'MMM d, yyyy')}
              </span>
              <Badge variant="outline" className="text-xs ml-1">
                {data.duration} day{data.duration !== 1 ? 's' : ''}
              </Badge>
            </div>
          ) : data.dueDate ? (
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3" />
              <span>Due: {format(data.dueDate, 'MMM d, yyyy')}</span>
            </div>
          ) : data.startDate ? (
            <div className="flex items-center gap-2">
              <Calendar className="h-3 w-3" />
              <span>Start: {format(data.startDate, 'MMM d, yyyy')}</span>
            </div>
          ) : null}
          <div>Phase: {data.phaseName}</div>
          <div>Responsibility: {data.responsibility}</div>
          {data.studyLabel && <div>Study: {data.studyLabel}</div>}
          {data.reportingEffortLabel && <div>Effort: {data.reportingEffortLabel}</div>}
          {data.comments && (
            <div className="text-xs italic mt-1 pt-1 border-t">
              {data.comments}
            </div>
          )}
        </div>
        <div className="mt-2">
          {data.isCompleted ? (
            <Badge variant="default" className="bg-green-500 text-xs">Completed</Badge>
          ) : data.isOverdue ? (
            <Badge variant="destructive" className="text-xs">Overdue</Badge>
          ) : (
            <Badge variant="secondary" className="text-xs">Pending</Badge>
          )}
        </div>
      </div>
    )
  }

  // Format x-axis ticks as dates
  const formatXAxis = (dayOffset: number) => {
    const date = addDays(dateRange.min, dayOffset)
    return format(date, 'MMM d')
  }

  // Get bar color based on status and phase
  const getBarColor = (entry: GanttDataPoint) => {
    if (entry.isCompleted) return STATUS_COLORS.completed
    if (entry.isOverdue) return STATUS_COLORS.overdue
    return phaseColorMap.get(entry.phaseName) || '#6b7280'
  }

  if (!chartData.length) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-lg">{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            No milestones with dates to display
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          {title}
          <Badge variant="outline" className="ml-auto">
            {chartData.length} milestone{chartData.length !== 1 ? 's' : ''}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {showLegend && (
          <div className="flex flex-wrap gap-4 mb-4 text-xs">
            <div className="flex items-center gap-4">
              <span className="text-muted-foreground font-medium">Phases:</span>
              {[...phaseColorMap.entries()].map(([phase, color]) => (
                <div key={phase} className="flex items-center gap-1">
                  <div
                    className="w-3 h-3 rounded-sm"
                    style={{ backgroundColor: color }}
                  />
                  <span>{phase}</span>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-4 border-l pl-4">
              <span className="text-muted-foreground font-medium">Status:</span>
              <div className="flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3 text-green-500" />
                <span>Completed</span>
              </div>
              <div className="flex items-center gap-1">
                <AlertTriangle className="h-3 w-3 text-red-500" />
                <span>Overdue</span>
              </div>
            </div>
          </div>
        )}

        <ResponsiveContainer width="100%" height={height}>
          <ComposedChart
            data={chartData}
            layout="vertical"
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
            <XAxis
              type="number"
              domain={[0, totalDays]}
              tickFormatter={formatXAxis}
              tick={{ fontSize: 11 }}
              ticks={Array.from({ length: Math.min(totalDays, 10) }, (_, i) =>
                Math.round((i * totalDays) / Math.min(totalDays - 1, 9))
              )}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={150}
              tick={{ fontSize: 10 }}
              tickFormatter={(value: string) =>
                value.length > 25 ? `${value.substring(0, 22)}...` : value
              }
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Today line */}
            {todayOffset !== null && (
              <ReferenceLine
                x={todayOffset}
                stroke={STATUS_COLORS.today}
                strokeWidth={2}
                strokeDasharray="4 4"
                label={{
                  value: 'Today',
                  position: 'top',
                  fill: STATUS_COLORS.today,
                  fontSize: 10,
                }}
              />
            )}

            {/* Invisible offset bar - pushes the visible bar to correct position */}
            <Bar
              dataKey="startOffset"
              stackId="timeline"
              fill="transparent"
              barSize={20}
            />

            {/* Visible duration bar */}
            <Bar
              dataKey="duration"
              stackId="timeline"
              barSize={20}
              radius={[4, 4, 4, 4]}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getBarColor(entry)}
                  opacity={entry.isCompleted ? 0.7 : 1}
                />
              ))}
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>

        {/* Summary stats */}
        <div className="flex gap-4 mt-4 pt-4 border-t text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>
              {chartData.filter(d => d.isCompleted).length} completed
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span>
              {chartData.filter(d => d.isOverdue).length} overdue
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span>
              {chartData.filter(d => !d.isCompleted && !d.isOverdue).length} upcoming
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Compact version for dashboard summaries
export function MilestoneGanttCompact({
  milestones,
  className,
}: {
  milestones: ReportingEffortMilestoneWithContext[]
  className?: string
}) {
  return (
    <MilestoneGantt
      milestones={milestones}
      title="Upcoming Milestones"
      showLegend={false}
      height={250}
      className={className}
    />
  )
}
