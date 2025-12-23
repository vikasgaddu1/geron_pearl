import { useQuery } from '@tanstack/react-query'
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
import { StatusBadge } from '@/components/common/StatusBadge'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { trackerApi } from '@/api'
import { ClipboardList, Clock, AlertTriangle, CheckCircle, PlayCircle } from 'lucide-react'
import type { ReportingEffortItemTracker } from '@/types'

interface ProgrammerDashboardProps {
  userId?: number | null
  userName?: string
}

export function ProgrammerDashboard({ userId, userName }: ProgrammerDashboardProps) {
  const { data: allTrackers = [], isLoading } = useQuery({
    queryKey: ['all-trackers'],
    queryFn: trackerApi.getAll,
  })

  // Filter trackers for the selected user
  const myTrackers = userId
    ? allTrackers.filter(
        (t) => t.primary_programmer_id === userId || t.qc_programmer_id === userId
      )
    : allTrackers

  // Calculate metrics
  const totalAssignments = myTrackers.length
  const notStarted = myTrackers.filter(
    (t) => t.production_status === 'NOT_STARTED' || t.qc_status === 'NOT_STARTED'
  ).length
  const inProgress = myTrackers.filter(
    (t) => t.production_status === 'IN_PROGRESS' || t.qc_status === 'IN_PROGRESS'
  ).length
  const completed = myTrackers.filter(
    (t) => t.production_status === 'COMPLETED' && t.qc_status === 'COMPLETED'
  ).length

  // Overdue items (items past due date that are not completed)
  const today = new Date()
  const overdue = myTrackers.filter((t) => {
    if (t.production_status !== 'COMPLETED' && t.production_due_date) {
      return new Date(t.production_due_date) < today
    }
    if (t.qc_status !== 'COMPLETED' && t.qc_due_date) {
      return new Date(t.qc_due_date) < today
    }
    return false
  }).length

  // Due soon (within 7 days)
  const weekFromNow = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000)
  const dueSoon = myTrackers.filter((t) => {
    if (t.production_status !== 'COMPLETED' && t.production_due_date) {
      const dueDate = new Date(t.production_due_date)
      return dueDate >= today && dueDate <= weekFromNow
    }
    if (t.qc_status !== 'COMPLETED' && t.qc_due_date) {
      const dueDate = new Date(t.qc_due_date)
      return dueDate >= today && dueDate <= weekFromNow
    }
    return false
  }).length

  if (isLoading) {
    return <PageLoader text="Loading assignments..." />
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

      {/* Assignments Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ClipboardList className="h-5 w-5" />
            {userId ? `Assignments for ${userName}` : 'All Assignments'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {myTrackers.length === 0 ? (
            <EmptyState
              icon={ClipboardList}
              title="No assignments"
              description={userId ? "This user has no assignments." : "No tracker assignments found."}
            />
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item Code</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Due Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {myTrackers.slice(0, 20).map((tracker) => {
                    const isPrimary = tracker.primary_programmer_id === userId
                    const isQC = tracker.qc_programmer_id === userId
                    const role = userId ? (isPrimary ? 'Primary' : isQC ? 'QC' : 'Both') : '-'
                    const status = isPrimary ? tracker.production_status : tracker.qc_status
                    const dueDate = isPrimary ? tracker.production_due_date : tracker.qc_due_date

                    return (
                      <TableRow key={tracker.id}>
                        <TableCell className="font-medium">{tracker.item_code}</TableCell>
                        <TableCell className="max-w-xs truncate">
                          {tracker.item_description || '-'}
                        </TableCell>
                        <TableCell>
                          <Badge variant={tracker.item_type === 'TLF' ? 'default' : 'secondary'}>
                            {tracker.item_subtype || tracker.item_type}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={role === 'Primary' ? 'default' : 'outline'}>
                            {role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={status} />
                        </TableCell>
                        <TableCell>
                          {dueDate ? new Date(dueDate).toLocaleDateString() : '-'}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
              {myTrackers.length > 20 && (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  Showing 20 of {myTrackers.length} assignments
                </div>
              )}
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

