import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/common/StatusBadge'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { trackerApi } from '@/api'
import { useAuthStore } from '@/stores/authStore'
import {
  ClipboardList,
  Clock,
  AlertTriangle,
  PlayCircle,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  PieChart as PieChartIcon,
  BarChart3,
  Target
} from 'lucide-react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'
import type { ReportingEffortItemTracker } from '@/types'
import { useState, useMemo } from 'react'

export function ProgrammerDashboard() {
  const { currentUser } = useAuthStore()
  const userId = currentUser?.id
  const navigate = useNavigate()
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())

  const { data: allTrackers = [], isLoading } = useQuery({
    queryKey: ['all-trackers'],
    queryFn: trackerApi.getAll,
  })

  // Filter trackers for the logged-in user
  // Use Number() to ensure type consistency (API might return string IDs)
  const myTrackers = userId
    ? allTrackers.filter(
        (t) => Number(t.production_programmer_id) === Number(userId) || Number(t.qc_programmer_id) === Number(userId)
      )
    : []

  // Group trackers by Study > Reporting Effort
  const groupedTrackers = useMemo(() => {
    const groups: Record<string, {
      studyLabel: string
      studyId?: number
      reportingEfforts: Record<string, {
        reportingEffortLabel: string
        reportingEffortId?: number
        databaseReleaseLabel?: string
        trackers: ReportingEffortItemTracker[]
      }>
    }> = {}

    myTrackers.forEach((tracker) => {
      const studyKey = tracker.study_label || 'Unknown Study'
      const reKey = tracker.reporting_effort_label || 'Unknown Reporting Effort'

      if (!groups[studyKey]) {
        groups[studyKey] = {
          studyLabel: studyKey,
          studyId: tracker.study_id,
          reportingEfforts: {}
        }
      }

      if (!groups[studyKey].reportingEfforts[reKey]) {
        groups[studyKey].reportingEfforts[reKey] = {
          reportingEffortLabel: reKey,
          reportingEffortId: tracker.reporting_effort_id,
          databaseReleaseLabel: tracker.database_release_label,
          trackers: []
        }
      }

      groups[studyKey].reportingEfforts[reKey].trackers.push(tracker)
    })

    return groups
  }, [myTrackers])

  const toggleGroup = (key: string) => {
    setCollapsedGroups(prev => {
      const newSet = new Set(prev)
      if (newSet.has(key)) {
        newSet.delete(key)
      } else {
        newSet.add(key)
      }
      return newSet
    })
  }

  // Navigate to tracker management with pre-selected filters
  const navigateToTracker = (tracker: ReportingEffortItemTracker) => {
    // Navigate to tracker management - the page will need to handle the query params
    const params = new URLSearchParams()
    if (tracker.study_id) params.set('studyId', String(tracker.study_id))
    if (tracker.reporting_effort_id) params.set('effortId', String(tracker.reporting_effort_id))
    navigate(`/tracker-management?${params.toString()}`)
  }

  // Calculate metrics
  const totalAssignments = myTrackers.length
  const notStarted = myTrackers.filter(
    (t) => t.production_status === 'not_started' || t.qc_status === 'not_started'
  ).length
  const inProgress = myTrackers.filter(
    (t) => t.production_status === 'in_progress' || t.qc_status === 'in_progress'
  ).length

  // Overdue items (items past due date that are not completed)
  const today = new Date()
  const overdue = myTrackers.filter((t) => {
    if (t.production_status !== 'completed' && t.due_date) {
      return new Date(t.due_date) < today
    }
    return false
  }).length

  // Due soon (within 7 days)
  const weekFromNow = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000)
  const dueSoon = myTrackers.filter((t) => {
    if (t.production_status !== 'completed' && t.due_date) {
      const dueDate = new Date(t.due_date)
      return dueDate >= today && dueDate <= weekFromNow
    }
    return false
  }).length

  // Chart data - Status breakdown
  const statusData = useMemo(() => {
    const statusCounts: Record<string, number> = {}
    myTrackers.forEach((t) => {
      const isProd = Number(t.production_programmer_id) === Number(userId)
      const status = isProd ? t.production_status : t.qc_status
      statusCounts[status] = (statusCounts[status] || 0) + 1
    })
    return Object.entries(statusCounts).map(([name, value]) => ({
      name: name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      value,
      key: name,
    }))
  }, [myTrackers, userId])

  // Chart data - Priority breakdown
  const priorityData = useMemo(() => {
    const priorityCounts: Record<string, number> = { critical: 0, high: 0, medium: 0, low: 0 }
    myTrackers.forEach((t) => {
      const priority = t.priority || 'medium'
      priorityCounts[priority] = (priorityCounts[priority] || 0) + 1
    })
    return Object.entries(priorityCounts)
      .filter(([_, value]) => value > 0)
      .map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value,
        key: name,
      }))
  }, [myTrackers])

  // Completion rate
  const completedCount = myTrackers.filter((t) => {
    const isProd = Number(t.production_programmer_id) === Number(userId)
    const status = isProd ? t.production_status : t.qc_status
    return status === 'completed'
  }).length
  const completionRate = totalAssignments > 0 ? Math.round((completedCount / totalAssignments) * 100) : 0

  // Color schemes
  const STATUS_COLORS: Record<string, string> = {
    not_started: '#6b7280',
    in_progress: '#3b82f6',
    ready_for_qc: '#8b5cf6',
    completed: '#22c55e',
    on_hold: '#eab308',
    failed: '#ef4444',
  }

  const PRIORITY_COLORS: Record<string, string> = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#22c55e',
  }

  if (isLoading) {
    return <PageLoader text="Loading your assignments..." />
  }

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <div className="grid gap-4 md:grid-cols-5">
        <MetricCard
          title="Total Assignments"
          value={totalAssignments}
          icon={ClipboardList}
        />
        <MetricCard
          title="Not Started"
          value={notStarted}
          icon={Clock}
          variant={notStarted > 0 ? 'warning' : 'default'}
        />
        <MetricCard
          title="In Progress"
          value={inProgress}
          icon={PlayCircle}
          variant="info"
        />
        <MetricCard
          title="Overdue"
          value={overdue}
          icon={AlertTriangle}
          variant={overdue > 0 ? 'danger' : 'default'}
        />
        <MetricCard
          title="Due in 7 Days"
          value={dueSoon}
          icon={Clock}
          variant={dueSoon > 0 ? 'warning' : 'default'}
        />
      </div>

      {/* Charts Row */}
      {myTrackers.length > 0 && (
        <div className="grid gap-6 md:grid-cols-3">
          {/* Completion Ring */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <Target className="h-4 w-4" />
                My Completion Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative h-40 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Completed', value: completedCount },
                        { name: 'Remaining', value: totalAssignments - completedCount },
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={45}
                      outerRadius={60}
                      dataKey="value"
                      startAngle={90}
                      endAngle={-270}
                    >
                      <Cell fill="#22c55e" />
                      <Cell fill="#e5e7eb" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-bold text-green-500">{completionRate}%</span>
                  <span className="text-xs text-muted-foreground">Complete</span>
                </div>
              </div>
              <div className="text-center text-sm text-muted-foreground mt-2">
                {completedCount} of {totalAssignments} items completed
              </div>
            </CardContent>
          </Card>

          {/* Status Distribution */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <PieChartIcon className="h-4 w-4" />
                Status Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      innerRadius={35}
                      outerRadius={55}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {statusData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={STATUS_COLORS[entry.key] || '#6b7280'}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number) => [`${value} items`, '']}
                      contentStyle={{ borderRadius: '8px', fontSize: '12px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 mt-2">
                {statusData.map((entry) => (
                  <div key={entry.key} className="flex items-center gap-1 text-xs">
                    <div
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: STATUS_COLORS[entry.key] || '#6b7280' }}
                    />
                    <span className="text-muted-foreground">{entry.name}: {entry.value}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Priority Distribution */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <BarChart3 className="h-4 w-4" />
                By Priority
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={priorityData}
                    layout="vertical"
                    margin={{ left: 10, right: 10 }}
                  >
                    <XAxis type="number" hide />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={60}
                      tick={{ fontSize: 11 }}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      formatter={(value: number) => [`${value} items`, '']}
                      contentStyle={{ borderRadius: '8px', fontSize: '12px' }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {priorityData.map((entry) => (
                        <Cell key={entry.key} fill={PRIORITY_COLORS[entry.key] || '#6b7280'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-center gap-3 mt-2">
                {priorityData.map((entry) => (
                  <div key={entry.key} className="flex items-center gap-1 text-xs">
                    <div
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: PRIORITY_COLORS[entry.key] }}
                    />
                    <span className="text-muted-foreground">{entry.name}: {entry.value}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Assignments Grouped by Study/Reporting Effort */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ClipboardList className="h-5 w-5" />
            My Assignments
          </CardTitle>
        </CardHeader>
        <CardContent>
          {myTrackers.length === 0 ? (
            <EmptyState
              icon={ClipboardList}
              title="No assignments"
              description="You don't have any tracker assignments yet."
            />
          ) : (
            <div className="space-y-4">
              {Object.entries(groupedTrackers).map(([studyKey, studyGroup]) => (
                <div key={studyKey} className="border rounded-lg overflow-hidden">
                  {/* Study Header */}
                  <div 
                    className="bg-muted/50 px-4 py-2 flex items-center justify-between cursor-pointer hover:bg-muted/70"
                    onClick={() => toggleGroup(studyKey)}
                  >
                    <div className="flex items-center gap-2">
                      {collapsedGroups.has(studyKey) ? (
                        <ChevronRight className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                      <span className="font-semibold text-sm">{studyGroup.studyLabel}</span>
                      <Badge variant="outline" className="text-xs">
                        {Object.values(studyGroup.reportingEfforts).reduce((sum, re) => sum + re.trackers.length, 0)} items
                      </Badge>
                    </div>
                  </div>

                  {!collapsedGroups.has(studyKey) && (
                    <div className="divide-y">
                      {Object.entries(studyGroup.reportingEfforts).map(([reKey, reGroup]) => (
                        <div key={reKey}>
                          {/* Reporting Effort Sub-header */}
                          <div className="bg-muted/30 px-6 py-1.5 flex items-center justify-between">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <span>{reGroup.reportingEffortLabel}</span>
                              {reGroup.databaseReleaseLabel && (
                                <span className="text-xs">({reGroup.databaseReleaseLabel})</span>
                              )}
                            </div>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              className="h-6 text-xs"
                              onClick={() => {
                                const firstTracker = reGroup.trackers[0]
                                if (firstTracker) navigateToTracker(firstTracker)
                              }}
                            >
                              <ExternalLink className="h-3 w-3 mr-1" />
                              Open Tracker
                            </Button>
                          </div>

                          {/* Trackers Table */}
                          <Table>
                            <TableHeader>
                              <TableRow className="hover:bg-transparent">
                                <TableHead className="w-32">Item Code</TableHead>
                                <TableHead>Title</TableHead>
                                <TableHead className="w-20">Type</TableHead>
                                <TableHead className="w-20">Priority</TableHead>
                                <TableHead className="w-24">Role</TableHead>
                                <TableHead className="w-28">Status</TableHead>
                                <TableHead className="w-28">Due Date</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {reGroup.trackers.map((tracker) => {
                                const isProd = Number(tracker.production_programmer_id) === Number(userId)
                                const isQC = Number(tracker.qc_programmer_id) === Number(userId)
                                const role = isProd && isQC ? 'Both' : isProd ? 'Production' : 'QC'
                                const status = isProd ? tracker.production_status : tracker.qc_status
                                const dueDate = tracker.due_date
                                const priorityColors: Record<string, string> = {
                                  critical: 'bg-red-500 text-white',
                                  high: 'bg-orange-500 text-white',
                                  medium: 'bg-yellow-500 text-black',
                                  low: 'bg-green-500 text-white',
                                }

                                return (
                                  <TableRow key={tracker.id} className="hover:bg-muted/30">
                                    <TableCell className="font-medium">{tracker.item_code}</TableCell>
                                    <TableCell className="max-w-xs truncate text-sm">
                                      {tracker.item_description || tracker.item_title || '-'}
                                    </TableCell>
                                    <TableCell>
                                      <Badge variant={tracker.item_type === 'TLF' ? 'default' : 'secondary'} className="text-xs">
                                        {tracker.item_subtype || tracker.item_type}
                                      </Badge>
                                    </TableCell>
                                    <TableCell>
                                      <Badge className={`text-xs ${priorityColors[tracker.priority || 'medium']}`}>
                                        {(tracker.priority || 'medium').charAt(0).toUpperCase() + (tracker.priority || 'medium').slice(1)}
                                      </Badge>
                                    </TableCell>
                                    <TableCell>
                                      <Badge variant={role === 'Production' ? 'default' : 'outline'} className="text-xs">
                                        {role}
                                      </Badge>
                                    </TableCell>
                                    <TableCell>
                                      <StatusBadge status={status} />
                                    </TableCell>
                                    <TableCell className="text-sm">
                                      {dueDate ? new Date(dueDate).toLocaleDateString() : '-'}
                                    </TableCell>
                                  </TableRow>
                                )
                              })}
                            </TableBody>
                          </Table>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

interface MetricCardProps {
  title: string
  value: number
  icon: React.ElementType
  variant?: 'default' | 'info' | 'warning' | 'danger' | 'success'
}

function MetricCard({ title, value, icon: Icon, variant = 'default' }: MetricCardProps) {
  const colorClasses = {
    default: 'text-primary',
    info: 'text-blue-500',
    warning: 'text-yellow-500',
    danger: 'text-red-500',
    success: 'text-green-500',
  }

  return (
    <Card>
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
}




