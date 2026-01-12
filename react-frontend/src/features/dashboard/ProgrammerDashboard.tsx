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
import { MetricCard } from '@/components/common/MetricCard'
import { DataTable, ColumnDef } from '@/components/common/DataTable'
import { trackerApi } from '@/api'
import { useAuthStore } from '@/stores/authStore'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
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
  Target,
  MessageSquareWarning,
  LayoutList,
  FolderTree,
  Search,
  X,
  Filter
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
import { useState, useMemo, useCallback } from 'react'
import {
  PRIORITY_BADGE_COLORS,
  PRIORITY_CHART_COLORS,
  STATUS_CHART_COLORS,
  ITEM_TYPE_CHART_COLORS,
  formatPriority,
} from '@/lib/constants'

export function ProgrammerDashboard() {
  const { currentUser } = useAuthStore()
  const userId = currentUser?.id
  const navigate = useNavigate()
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'grouped' | 'flat'>('grouped')
  
  // Filter state
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [priorityFilter, setPriorityFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [studyFilter, setStudyFilter] = useState<string>('all')
  const [roleFilter, setRoleFilter] = useState<string>('all')

  const { data: allTrackers = [], isLoading } = useQuery({
    queryKey: ['all-trackers'],
    queryFn: trackerApi.getAll,
  })

  // Filter trackers for the logged-in user
  // Use Number() to ensure type consistency (API might return string IDs)
  const myTrackers = useMemo(() => {
    if (!userId) return []
    return allTrackers.filter(
      (t) => Number(t.production_programmer_id) === Number(userId) || Number(t.qc_programmer_id) === Number(userId)
    )
  }, [userId, allTrackers])

  // Get unique values for filter dropdowns
  const filterOptions = useMemo(() => {
    const studies = [...new Set(myTrackers.map(t => t.study_label).filter(Boolean))]
    const types = [...new Set(myTrackers.map(t => t.item_subtype || t.item_type).filter(Boolean))]
    return { studies, types }
  }, [myTrackers])

  // Apply filters to myTrackers
  const filteredTrackers = useMemo(() => {
    return myTrackers.filter((tracker) => {
      const isProd = Number(tracker.production_programmer_id) === Number(userId)
      const isQC = Number(tracker.qc_programmer_id) === Number(userId)
      const role = isProd && isQC ? 'Both' : isProd ? 'Production' : 'QC'
      const myStatus = isProd ? tracker.production_status : tracker.qc_status

      // Text search (item code or title)
      if (searchText) {
        const searchLower = searchText.toLowerCase()
        const matchesCode = tracker.item_code?.toLowerCase().includes(searchLower)
        const matchesTitle = tracker.item_title?.toLowerCase().includes(searchLower)
        if (!matchesCode && !matchesTitle) return false
      }

      // Status filter
      if (statusFilter !== 'all' && myStatus !== statusFilter) return false

      // Priority filter
      if (priorityFilter !== 'all' && tracker.priority !== priorityFilter) return false

      // Type filter (subtype or type)
      if (typeFilter !== 'all') {
        const trackerType = tracker.item_subtype || tracker.item_type
        if (trackerType !== typeFilter) return false
      }

      // Study filter
      if (studyFilter !== 'all' && tracker.study_label !== studyFilter) return false

      // Role filter
      if (roleFilter !== 'all' && role !== roleFilter) return false

      return true
    })
  }, [myTrackers, userId, searchText, statusFilter, priorityFilter, typeFilter, studyFilter, roleFilter])

  // Check if any filters are active
  const hasActiveFilters = searchText || statusFilter !== 'all' || priorityFilter !== 'all' || 
                           typeFilter !== 'all' || studyFilter !== 'all' || roleFilter !== 'all'

  // Clear all filters
  const clearFilters = () => {
    setSearchText('')
    setStatusFilter('all')
    setPriorityFilter('all')
    setTypeFilter('all')
    setStudyFilter('all')
    setRoleFilter('all')
  }

  // Group trackers by Study > Reporting Effort > Item Type
  const groupedTrackers = useMemo(() => {
    const groups: Record<string, {
      studyLabel: string
      studyId?: number
      reportingEfforts: Record<string, {
        reportingEffortLabel: string
        reportingEffortId?: number
        databaseReleaseLabel?: string
        itemTypes: Record<string, {
          typeLabel: string
          trackers: ReportingEffortItemTracker[]
        }>
      }>
    }> = {}

    filteredTrackers.forEach((tracker) => {
      const studyKey = tracker.study_label || 'Unknown Study'
      const reKey = tracker.reporting_effort_label || 'Unknown Reporting Effort'
      // Group by item_type (TLF or Dataset), with subtype as label
      const itemType = tracker.item_type || 'Unknown'
      const typeKey = itemType
      // Create a friendly label: "TLF (Tables, Listings, Figures)" or "Dataset (SDTM/ADaM)"
      const getTypeLabel = (type: string, subtype?: string) => {
        if (type === 'TLF') {
          return subtype ? `${subtype.charAt(0).toUpperCase() + subtype.slice(1)}s` : 'TLFs'
        } else if (type === 'Dataset') {
          return subtype ? `${subtype.toUpperCase()} Datasets` : 'Datasets'
        }
        return type
      }

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
          itemTypes: {}
        }
      }

      // Further group by item subtype for better organization
      const subtypeKey = tracker.item_subtype || typeKey
      if (!groups[studyKey].reportingEfforts[reKey].itemTypes[subtypeKey]) {
        groups[studyKey].reportingEfforts[reKey].itemTypes[subtypeKey] = {
          typeLabel: getTypeLabel(itemType, tracker.item_subtype),
          trackers: []
        }
      }

      groups[studyKey].reportingEfforts[reKey].itemTypes[subtypeKey].trackers.push(tracker)
    })

    return groups
  }, [filteredTrackers])

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

  // Prepare flat list data with computed fields for DataTable
  const flatListData = useMemo(() => {
    return filteredTrackers.map((tracker) => {
      const isProd = Number(tracker.production_programmer_id) === Number(userId)
      const isQC = Number(tracker.qc_programmer_id) === Number(userId)
      const role = isProd && isQC ? 'Both' : isProd ? 'Production' : 'QC'
      const status = isProd ? tracker.production_status : tracker.qc_status
      
      return {
        ...tracker,
        role,
        myStatus: status,
        studyLabel: tracker.study_label || 'Unknown',
        typeLabel: tracker.item_subtype 
          ? (tracker.item_type === 'TLF' 
            ? `${tracker.item_subtype.charAt(0).toUpperCase() + tracker.item_subtype.slice(1)}` 
            : tracker.item_subtype.toUpperCase())
          : tracker.item_type || 'Unknown',
      }
    })
  }, [filteredTrackers, userId])

  // Navigate to tracker management with pre-selected filters
  const navigateToTracker = useCallback((tracker: ReportingEffortItemTracker, includeItemCode = false) => {
    // Navigate to tracker management - the page will need to handle the query params
    const params = new URLSearchParams()
    if (tracker.study_id) params.set('studyId', String(tracker.study_id))
    if (tracker.reporting_effort_id) params.set('effortId', String(tracker.reporting_effort_id))
    if (includeItemCode && tracker.item_code) params.set('itemCode', tracker.item_code)
    // Include item subtype to auto-select the correct tab (TLF, SDTM, or ADaM)
    if (includeItemCode && tracker.item_subtype) params.set('itemSubtype', tracker.item_subtype)
    navigate(`/tracker-management?${params.toString()}`)
  }, [navigate])

  // Define columns for the flat list DataTable
  const flatListColumns: ColumnDef<typeof flatListData[0]>[] = useMemo(() => [
    {
      id: 'item_code',
      header: 'Item Code',
      accessorKey: 'item_code',
      filterType: 'text',
      cell: (value) => <span className="font-medium">{value}</span>,
    },
    {
      id: 'item_title',
      header: 'Title',
      accessorKey: 'item_title',
      filterType: 'text',
      cell: (value) => <span className="max-w-xs truncate text-sm">{value || '-'}</span>,
    },
    {
      id: 'studyLabel',
      header: 'Study',
      accessorKey: 'studyLabel',
      filterType: 'select',
    },
    {
      id: 'typeLabel',
      header: 'Type',
      accessorKey: 'typeLabel',
      filterType: 'select',
      cell: (value, row) => (
        <Badge variant={row.item_type === 'TLF' ? 'default' : 'secondary'} className="text-xs">
          {value}
        </Badge>
      ),
    },
    {
      id: 'priority',
      header: 'Priority',
      accessorKey: 'priority',
      filterType: 'select',
      filterOptions: ['critical', 'high', 'medium', 'low'],
      cell: (value) => {
        const priority = value || 'medium'
        return (
          <Badge className={`text-xs ${PRIORITY_BADGE_COLORS[priority]}`}>
            {formatPriority(priority)}
          </Badge>
        )
      },
    },
    {
      id: 'role',
      header: 'Role',
      accessorKey: 'role',
      filterType: 'select',
      filterOptions: ['Production', 'QC', 'Both'],
      cell: (value) => (
        <Badge variant={value === 'Production' ? 'default' : 'outline'} className="text-xs">
          {value}
        </Badge>
      ),
    },
    {
      id: 'myStatus',
      header: 'Status',
      accessorKey: 'myStatus',
      filterType: 'select',
      filterOptions: ['not_started', 'in_progress', 'ready_for_qc', 'completed', 'on_hold', 'failed'],
      cell: (value) => <StatusBadge status={value} />,
    },
    {
      id: 'due_date',
      header: 'Due Date',
      accessorKey: 'due_date',
      filterType: 'date',
      cell: (value) => (
        <span className="text-sm">{value ? new Date(value).toLocaleDateString() : '-'}</span>
      ),
    },
    {
      id: 'unresolved_comment_count',
      header: 'Comments',
      accessorKey: 'unresolved_comment_count',
      enableSorting: true,
      cell: (value) => (
        value > 0 ? (
          <Badge variant="destructive" className="text-xs">{value}</Badge>
        ) : (
          <span className="text-muted-foreground text-xs">-</span>
        )
      ),
    },
    {
      id: 'actions',
      header: '',
      accessorKey: 'id',
      enableSorting: false,
      cell: (_value, row) => (
        <Button
          variant="ghost"
          size="sm"
          className="h-7 text-xs"
          onClick={(e) => {
            e.stopPropagation()
            navigateToTracker(row, true)
          }}
        >
          <ExternalLink className="h-3 w-3" />
        </Button>
      ),
    },
  ], [navigateToTracker])

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

  // Count of items with unresolved comments (for metric card)
  const unresolvedCommentsCount = useMemo(() => {
    return myTrackers.filter((t) => (t.unresolved_comment_count || 0) > 0).length
  }, [myTrackers])

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

  // Chart data - Item Type breakdown
  const itemTypeData = useMemo(() => {
    const typeCounts: Record<string, number> = {}
    myTrackers.forEach((t) => {
      // Use subtype for more granular breakdown (table/listing/figure/SDTM/ADaM)
      const typeKey = t.item_subtype || t.item_type || 'Unknown'
      typeCounts[typeKey] = (typeCounts[typeKey] || 0) + 1
    })
    return Object.entries(typeCounts)
      .map(([name, value]) => ({
        name: name === 'table' ? 'Tables' : 
              name === 'listing' ? 'Listings' : 
              name === 'figure' ? 'Figures' : 
              name === 'SDTM' ? 'SDTM' : 
              name === 'ADaM' ? 'ADaM' : name,
        value,
        key: name,
      }))
      .sort((a, b) => b.value - a.value)
  }, [myTrackers])

  // Completion rate
  const completedCount = myTrackers.filter((t) => {
    const isProd = Number(t.production_programmer_id) === Number(userId)
    const status = isProd ? t.production_status : t.qc_status
    return status === 'completed'
  }).length
  const completionRate = totalAssignments > 0 ? Math.round((completedCount / totalAssignments) * 100) : 0

  if (isLoading) {
    return <PageLoader text="Loading your assignments..." />
  }

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <div className="grid gap-4 md:grid-cols-6">
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
        <MetricCard
          title="Unresolved Comments"
          value={unresolvedCommentsCount}
          icon={MessageSquareWarning}
          variant={unresolvedCommentsCount > 0 ? 'danger' : 'default'}
        />
      </div>

      {/* Charts Row */}
      {myTrackers.length > 0 && (
        <div className="grid gap-6 md:grid-cols-4">
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
                          fill={STATUS_CHART_COLORS[entry.key] || '#6b7280'}
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
                      style={{ backgroundColor: STATUS_CHART_COLORS[entry.key] || '#6b7280' }}
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
                        <Cell key={entry.key} fill={PRIORITY_CHART_COLORS[entry.key] || '#6b7280'} />
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
                      style={{ backgroundColor: PRIORITY_CHART_COLORS[entry.key] }}
                    />
                    <span className="text-muted-foreground">{entry.name}: {entry.value}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Item Type Distribution */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <BarChart3 className="h-4 w-4" />
                By Item Type
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={itemTypeData}
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
                      {itemTypeData.map((entry) => (
                        <Cell key={entry.key} fill={ITEM_TYPE_CHART_COLORS[entry.key] || '#6b7280'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-2">
                {itemTypeData.map((entry) => (
                  <div key={entry.key} className="flex items-center gap-1 text-xs">
                    <div
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: ITEM_TYPE_CHART_COLORS[entry.key] || '#6b7280' }}
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
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5" />
              My Assignments
            </CardTitle>
            {myTrackers.length > 0 && (
              <div className="flex items-center gap-1 bg-muted rounded-lg p-1">
                <Button
                  variant={viewMode === 'grouped' ? 'default' : 'ghost'}
                  size="sm"
                  className="h-7 px-3"
                  onClick={() => setViewMode('grouped')}
                >
                  <FolderTree className="h-4 w-4 mr-1" />
                  Grouped
                </Button>
                <Button
                  variant={viewMode === 'flat' ? 'default' : 'ghost'}
                  size="sm"
                  className="h-7 px-3"
                  onClick={() => setViewMode('flat')}
                >
                  <LayoutList className="h-4 w-4 mr-1" />
                  Flat List
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {myTrackers.length === 0 ? (
            <EmptyState
              icon={ClipboardList}
              title="No assignments"
              description="You don't have any tracker assignments yet."
            />
          ) : (
            <>
              {/* Filter Bar */}
              <div className="mb-4 space-y-3">
                <div className="flex items-center gap-2 flex-wrap">
                  {/* Search */}
                  <div className="relative flex-1 min-w-[200px] max-w-[300px]">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search item code or title..."
                      value={searchText}
                      onChange={(e) => setSearchText(e.target.value)}
                      className="pl-8 h-9"
                    />
                    {searchText && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6"
                        onClick={() => setSearchText('')}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    )}
                  </div>

                  {/* Status Filter */}
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[140px] h-9">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      <SelectItem value="not_started">Not Started</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="ready_for_qc">Ready for QC</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="on_hold">On Hold</SelectItem>
                      <SelectItem value="failed">Failed</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Priority Filter */}
                  <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                    <SelectTrigger className="w-[130px] h-9">
                      <SelectValue placeholder="Priority" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Priorities</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Type Filter */}
                  <Select value={typeFilter} onValueChange={setTypeFilter}>
                    <SelectTrigger className="w-[130px] h-9">
                      <SelectValue placeholder="Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      {filterOptions.types.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type === 'table' ? 'Table' : 
                           type === 'listing' ? 'Listing' : 
                           type === 'figure' ? 'Figure' : 
                           type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {/* Study Filter */}
                  {filterOptions.studies.length > 1 && (
                    <Select value={studyFilter} onValueChange={setStudyFilter}>
                      <SelectTrigger className="w-[150px] h-9">
                        <SelectValue placeholder="Study" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Studies</SelectItem>
                        {filterOptions.studies.map((study) => (
                          <SelectItem key={study} value={study!}>
                            {study}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}

                  {/* Role Filter */}
                  <Select value={roleFilter} onValueChange={setRoleFilter}>
                    <SelectTrigger className="w-[130px] h-9">
                      <SelectValue placeholder="Role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Roles</SelectItem>
                      <SelectItem value="Production">Production</SelectItem>
                      <SelectItem value="QC">QC</SelectItem>
                      <SelectItem value="Both">Both</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Clear Filters */}
                  {hasActiveFilters && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearFilters}
                      className="h-9 px-3"
                    >
                      <X className="h-4 w-4 mr-1" />
                      Clear
                    </Button>
                  )}
                </div>

                {/* Active Filters Summary */}
                {hasActiveFilters && (
                  <div className="flex items-center gap-2 text-sm">
                    <Filter className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">
                      Showing {filteredTrackers.length} of {myTrackers.length} items
                    </span>
                    {filteredTrackers.length === 0 && (
                      <span className="text-yellow-600">— No items match your filters</span>
                    )}
                  </div>
                )}
              </div>

              {/* Content */}
              {filteredTrackers.length === 0 && hasActiveFilters ? (
                <EmptyState
                  icon={Filter}
                  title="No matching items"
                  description="Try adjusting your filters to see more results."
                />
              ) : viewMode === 'flat' ? (
            <DataTable
              data={flatListData}
              columns={flatListColumns}
              enablePagination={true}
              defaultPageSize={25}
              pageSizeOptions={[10, 25, 50, 100]}
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
                        {Object.values(studyGroup.reportingEfforts).reduce((sum, re) => 
                          sum + Object.values(re.itemTypes).reduce((typeSum, t) => typeSum + t.trackers.length, 0), 0)} items
                      </Badge>
                    </div>
                  </div>

                  {!collapsedGroups.has(studyKey) && (
                    <div className="divide-y">
                      {Object.entries(studyGroup.reportingEfforts).map(([reKey, reGroup]) => {
                        const reGroupKey = `${studyKey}-${reKey}`
                        const totalItems = Object.values(reGroup.itemTypes).reduce((sum, t) => sum + t.trackers.length, 0)
                        
                        return (
                          <div key={reKey}>
                            {/* Reporting Effort Sub-header */}
                            <div 
                              className="bg-muted/30 px-6 py-1.5 flex items-center justify-between cursor-pointer hover:bg-muted/40"
                              onClick={() => toggleGroup(reGroupKey)}
                            >
                              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                {collapsedGroups.has(reGroupKey) ? (
                                  <ChevronRight className="h-3 w-3" />
                                ) : (
                                  <ChevronDown className="h-3 w-3" />
                                )}
                                <span className="font-medium">{reGroup.reportingEffortLabel}</span>
                                {reGroup.databaseReleaseLabel && (
                                  <span className="text-xs">({reGroup.databaseReleaseLabel})</span>
                                )}
                                <Badge variant="outline" className="text-xs ml-2">
                                  {totalItems} items
                                </Badge>
                              </div>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                className="h-6 text-xs"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  const firstType = Object.values(reGroup.itemTypes)[0]
                                  const firstTracker = firstType?.trackers[0]
                                  if (firstTracker) navigateToTracker(firstTracker)
                                }}
                              >
                                <ExternalLink className="h-3 w-3 mr-1" />
                                Open Tracker
                              </Button>
                            </div>

                            {/* Item Types within Reporting Effort */}
                            {!collapsedGroups.has(reGroupKey) && Object.entries(reGroup.itemTypes).map(([typeKey, typeGroup]) => (
                              <div key={typeKey}>
                                {/* Type Sub-header */}
                                <div className="bg-blue-50/50 dark:bg-blue-950/20 px-8 py-1 flex items-center gap-2 border-l-2 border-blue-500">
                                  <Badge variant={typeKey === 'table' || typeKey === 'listing' || typeKey === 'figure' ? 'default' : 'secondary'} className="text-xs">
                                    {typeGroup.typeLabel}
                                  </Badge>
                                  <span className="text-xs text-muted-foreground">
                                    ({typeGroup.trackers.length} items)
                                  </span>
                                </div>

                                {/* Trackers Table */}
                                <Table>
                                  <TableHeader>
                                    <TableRow className="hover:bg-transparent">
                                      <TableHead className="w-28">Item Code</TableHead>
                                      <TableHead>Title</TableHead>
                                      <TableHead className="w-20">Priority</TableHead>
                                      <TableHead className="w-24">Role</TableHead>
                                      <TableHead className="w-28">Status</TableHead>
                                      <TableHead className="w-24">Due Date</TableHead>
                                      <TableHead className="w-24 text-center">Comments</TableHead>
                                      <TableHead className="w-16"></TableHead>
                                    </TableRow>
                                  </TableHeader>
                                  <TableBody>
                                    {typeGroup.trackers.map((tracker) => {
                                      const isProd = Number(tracker.production_programmer_id) === Number(userId)
                                      const isQC = Number(tracker.qc_programmer_id) === Number(userId)
                                      const role = isProd && isQC ? 'Both' : isProd ? 'Production' : 'QC'
                                      const status = isProd ? tracker.production_status : tracker.qc_status
                                      const dueDate = tracker.due_date
                                      const commentCount = tracker.unresolved_comment_count || 0

                                      return (
                                        <TableRow
                                          key={tracker.id}
                                          className="hover:bg-muted/50 cursor-pointer"
                                          onClick={() => navigateToTracker(tracker, true)}
                                        >
                                          <TableCell className="font-medium">{tracker.item_code}</TableCell>
                                          <TableCell className="max-w-xs truncate text-sm">
                                            {tracker.item_title || '-'}
                                          </TableCell>
                                          <TableCell>
                                            <Badge className={`text-xs ${PRIORITY_BADGE_COLORS[tracker.priority || 'medium']}`}>
                                              {formatPriority(tracker.priority)}
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
                                          <TableCell className="text-center">
                                            {commentCount > 0 ? (
                                              <Badge variant="destructive" className="text-xs">
                                                {commentCount}
                                              </Badge>
                                            ) : (
                                              <span className="text-muted-foreground text-xs">-</span>
                                            )}
                                          </TableCell>
                                          <TableCell>
                                            <Button 
                                              variant="ghost" 
                                              size="sm"
                                              className="h-7 text-xs"
                                              onClick={(e) => {
                                                e.stopPropagation()
                                                navigateToTracker(tracker, true)
                                              }}
                                            >
                                              <ExternalLink className="h-3 w-3" />
                                            </Button>
                                          </TableCell>
                                        </TableRow>
                                      )
                                    })}
                                  </TableBody>
                                </Table>
                              </div>
                            ))}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}





