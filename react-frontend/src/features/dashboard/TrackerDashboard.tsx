import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { reportingEffortsApi, trackerApi, usersApi } from '@/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { Filter, BarChart3, PieChartIcon, Users } from 'lucide-react'
import type { TrackerStatus } from '@/types'

const STATUS_COLORS: Record<TrackerStatus, string> = {
  NOT_STARTED: '#6b7280',
  IN_PROGRESS: '#3b82f6',
  COMPLETED: '#22c55e',
  ON_HOLD: '#eab308',
  FAILED: '#ef4444',
}

export function TrackerDashboard() {
  const [selectedEffortId, setSelectedEffortId] = useState<string>('all')

  const { data: efforts = [] } = useQuery({
    queryKey: ['reporting-efforts'],
    queryFn: reportingEffortsApi.getAll,
  })

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.getAll,
  })

  const { data: trackers = [], isLoading } = useQuery({
    queryKey: ['trackers-dashboard', selectedEffortId],
    queryFn: () => (selectedEffortId && selectedEffortId !== 'all' ? trackerApi.getByEffortBulk(Number(selectedEffortId)) : trackerApi.getAll()),
  })

  // Group efforts by study and database release for better display
  const groupedEfforts = useMemo(() => {
    const groups: Record<string, Record<string, typeof efforts>> = {}
    efforts.forEach(effort => {
      const studyLabel = effort.study_label || 'Unknown Study'
      const dbLabel = effort.database_release_label_full || 'Unknown DB'
      if (!groups[studyLabel]) groups[studyLabel] = {}
      if (!groups[studyLabel][dbLabel]) groups[studyLabel][dbLabel] = []
      groups[studyLabel][dbLabel].push(effort)
    })
    return groups
  }, [efforts])

  // Calculate statistics
  const totalItems = trackers.length
  const completed = trackers.filter((t) => t.production_status === 'COMPLETED' && t.qc_status === 'COMPLETED').length
  const inProgress = trackers.filter((t) => t.production_status === 'IN_PROGRESS' || t.qc_status === 'IN_PROGRESS').length
  const completionRate = totalItems > 0 ? Math.round((completed / totalItems) * 100) : 0

  // Status breakdown for pie chart
  const productionStatusData = Object.entries(
    trackers.reduce((acc, t) => {
      acc[t.production_status] = (acc[t.production_status] || 0) + 1
      return acc
    }, {} as Record<string, number>)
  ).map(([name, value]) => ({ name: name.replace('_', ' '), value }))

  const qcStatusData = Object.entries(
    trackers.reduce((acc, t) => {
      acc[t.qc_status] = (acc[t.qc_status] || 0) + 1
      return acc
    }, {} as Record<string, number>)
  ).map(([name, value]) => ({ name: name.replace('_', ' '), value }))

  // Task type breakdown for bar chart
  const taskTypeData = Object.entries(
    trackers.reduce((acc, t) => {
      const type = t.item_subtype || t.item_type || 'Unknown'
      if (!acc[type]) acc[type] = { total: 0, completed: 0, inProgress: 0 }
      acc[type].total++
      if (t.production_status === 'COMPLETED') acc[type].completed++
      if (t.production_status === 'IN_PROGRESS') acc[type].inProgress++
      return acc
    }, {} as Record<string, { total: number; completed: number; inProgress: number }>)
  ).map(([name, data]) => ({ name, ...data }))

  // Programmer workload
  const workloadData = users
    .filter((u) => ['programmer', 'lead', 'analyst'].includes(u.role))
    .map((user) => {
      const primary = trackers.filter((t) => t.primary_programmer_id === user.id).length
      const qc = trackers.filter((t) => t.qc_programmer_id === user.id).length
      return { name: user.username, primary, qc, total: primary + qc }
    })
    .filter((w) => w.total > 0)
    .sort((a, b) => b.total - a.total)

  if (isLoading) {
    return <PageLoader text="Loading dashboard..." />
  }

  return (
    <div className="space-y-6">
      {/* Effort Selector */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filter by Reporting Effort
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="w-full md:w-[600px]">
            <Label className="text-sm font-medium mb-1.5 block">Reporting Effort</Label>
            <Select value={selectedEffortId} onValueChange={setSelectedEffortId}>
              <SelectTrigger>
                <SelectValue placeholder="All Reporting Efforts" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Reporting Efforts</SelectItem>
                {Object.entries(groupedEfforts).map(([studyLabel, dbGroups]) => (
                  Object.entries(dbGroups).map(([dbLabel, effortsList]) => (
                    effortsList.map((effort) => (
                      <SelectItem key={effort.id} value={String(effort.id)}>
                        {studyLabel} → {dbLabel} → {effort.database_release_label}
                      </SelectItem>
                    ))
                  ))
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Row */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-primary">{efforts.length}</p>
            <p className="text-sm text-muted-foreground">Total Studies</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-primary">{totalItems}</p>
            <p className="text-sm text-muted-foreground">Active Trackers</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-primary">{totalItems}</p>
            <p className="text-sm text-muted-foreground">Total Items</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-green-500">{completionRate}%</p>
            <p className="text-sm text-muted-foreground">Completion Rate</p>
          </CardContent>
        </Card>
      </div>

      {trackers.length === 0 ? (
        <EmptyState
          icon={BarChart3}
          title="No data available"
          description="Select a reporting effort or add tracker data to see analytics."
        />
      ) : (
        <>
          {/* Task Type Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Task Type Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={taskTypeData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="completed" fill="#22c55e" name="Completed" />
                      <Bar dataKey="inProgress" fill="#3b82f6" name="In Progress" />
                      <Bar dataKey="total" fill="#6b7280" name="Total" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Type</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                        <TableHead className="text-right">Completed</TableHead>
                        <TableHead className="text-right">In Progress</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {taskTypeData.map((row) => (
                        <TableRow key={row.name}>
                          <TableCell className="font-medium">{row.name}</TableCell>
                          <TableCell className="text-right">{row.total}</TableCell>
                          <TableCell className="text-right text-green-600">{row.completed}</TableCell>
                          <TableCell className="text-right text-blue-600">{row.inProgress}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Status Charts */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChartIcon className="h-5 w-5" />
                  Production Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={productionStatusData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      >
                        {productionStatusData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={STATUS_COLORS[entry.name.replace(' ', '_') as TrackerStatus] || '#6b7280'}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChartIcon className="h-5 w-5" />
                  QC Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={qcStatusData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      >
                        {qcStatusData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={STATUS_COLORS[entry.name.replace(' ', '_') as TrackerStatus] || '#6b7280'}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Programmer Workload */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Programmer Workload
              </CardTitle>
            </CardHeader>
            <CardContent>
              {workloadData.length === 0 ? (
                <EmptyState
                  icon={Users}
                  title="No workload data"
                  description="Assign programmers to trackers to see workload distribution."
                />
              ) : (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Programmer</TableHead>
                        <TableHead className="text-right">Primary</TableHead>
                        <TableHead className="text-right">QC</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {workloadData.map((row) => (
                        <TableRow key={row.name}>
                          <TableCell className="font-medium">{row.name}</TableCell>
                          <TableCell className="text-right">
                            <Badge variant="default">{row.primary}</Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Badge variant="outline">{row.qc}</Badge>
                          </TableCell>
                          <TableCell className="text-right font-bold">{row.total}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}


