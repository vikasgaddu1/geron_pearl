import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { TooltipWrapper } from '@/components/common/TooltipWrapper'
import { MilestoneGantt } from '@/components/charts/MilestoneGantt'
import { reportingEffortsApi, trackerApi, studiesApi, databaseReleasesApi, milestonesApi } from '@/api'
import {
  ChevronDown,
  ChevronRight,
  BarChart3,
  FolderOpen,
  Database,
  FileText,
  CheckCircle2,
  Clock,
  AlertCircle,
  Pause,
  XCircle,
  CircleDot,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ReportingEffortItemTracker } from '@/types'

const STATUS_CONFIG = {
  not_started: { label: 'Not Started', color: 'bg-gray-400', icon: CircleDot },
  in_progress: { label: 'In Progress', color: 'bg-blue-500', icon: Clock },
  ready_for_qc: { label: 'Ready for QC', color: 'bg-purple-500', icon: AlertCircle },
  completed: { label: 'Completed', color: 'bg-green-500', icon: CheckCircle2 },
  on_hold: { label: 'On Hold', color: 'bg-yellow-500', icon: Pause },
  failed: { label: 'Failed', color: 'bg-red-500', icon: XCircle },
}

interface ProgressStats {
  total: number
  not_started: number
  in_progress: number
  ready_for_qc: number
  completed: number
  on_hold: number
  failed: number
}

// Determine tracker type from item: TLF, SDTM, or ADAM
function getTrackerType(item: ReportingEffortItemTracker): 'TLF' | 'SDTM' | 'ADAM' {
  if (item.item_type === 'TLF') return 'TLF'
  if (item.item_subtype === 'SDTM') return 'SDTM'
  if (item.item_subtype === 'ADaM') return 'ADAM'
  // Default based on item_type
  return item.item_type === 'Dataset' ? 'SDTM' : 'TLF'
}

interface TrackerGroup {
  type: 'TLF' | 'SDTM' | 'ADAM'
  items: ReportingEffortItemTracker[]
  stats: ProgressStats
}

function groupItemsIntoTrackers(items: ReportingEffortItemTracker[]): TrackerGroup[] {
  const grouped: Record<string, ReportingEffortItemTracker[]> = {}

  items.forEach(item => {
    const type = getTrackerType(item)
    if (!grouped[type]) grouped[type] = []
    grouped[type].push(item)
  })

  return Object.entries(grouped).map(([type, typeItems]) => ({
    type: type as 'TLF' | 'SDTM' | 'ADAM',
    items: typeItems,
    stats: calculateStats(typeItems),
  }))
}

function calculateStats(items: ReportingEffortItemTracker[]): ProgressStats {
  const stats: ProgressStats = {
    total: items.length,
    not_started: 0,
    in_progress: 0,
    ready_for_qc: 0,
    completed: 0,
    on_hold: 0,
    failed: 0,
  }

  items.forEach(t => {
    // Use production_status as the primary indicator
    const status = t.production_status as keyof typeof STATUS_CONFIG
    if (status in stats) {
      stats[status]++
    }
  })

  return stats
}

function ProgressBar({ stats, showLabels = false }: { stats: ProgressStats; showLabels?: boolean }) {
  if (stats.total === 0) return null

  const segments = [
    { key: 'completed', ...STATUS_CONFIG.completed, count: stats.completed },
    { key: 'ready_for_qc', ...STATUS_CONFIG.ready_for_qc, count: stats.ready_for_qc },
    { key: 'in_progress', ...STATUS_CONFIG.in_progress, count: stats.in_progress },
    { key: 'on_hold', ...STATUS_CONFIG.on_hold, count: stats.on_hold },
    { key: 'failed', ...STATUS_CONFIG.failed, count: stats.failed },
    { key: 'not_started', ...STATUS_CONFIG.not_started, count: stats.not_started },
  ].filter(s => s.count > 0)

  return (
    <div className="space-y-1">
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-muted">
        {segments.map((segment) => (
          <TooltipWrapper
            key={segment.key}
            content={`${segment.label}: ${segment.count} (${Math.round((segment.count / stats.total) * 100)}%)`}
          >
            <div
              className={cn(segment.color, 'h-full transition-all')}
              style={{ width: `${(segment.count / stats.total) * 100}%` }}
            />
          </TooltipWrapper>
        ))}
      </div>
      {showLabels && (
        <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
          {segments.map((segment) => (
            <div key={segment.key} className="flex items-center gap-1">
              <div className={cn('h-2 w-2 rounded-full', segment.color)} />
              <span>{segment.label}: {segment.count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function CompletionBadge({ stats }: { stats: ProgressStats }) {
  if (stats.total === 0) return <Badge variant="secondary">No items</Badge>

  const completionRate = Math.round((stats.completed / stats.total) * 100)

  if (completionRate === 100) {
    return <Badge className="bg-green-500">100% Complete</Badge>
  } else if (completionRate >= 75) {
    return <Badge className="bg-green-600">{completionRate}%</Badge>
  } else if (completionRate >= 50) {
    return <Badge className="bg-blue-500">{completionRate}%</Badge>
  } else if (completionRate >= 25) {
    return <Badge className="bg-yellow-500">{completionRate}%</Badge>
  } else {
    return <Badge variant="secondary">{completionRate}%</Badge>
  }
}

export function TrackerDashboard() {
  const [expandedStudies, setExpandedStudies] = useState<Set<number>>(new Set())
  const [expandedReleases, setExpandedReleases] = useState<Set<number>>(new Set())

  const { data: studies = [] } = useQuery({
    queryKey: ['studies'],
    queryFn: studiesApi.getAll,
  })

  const { data: releases = [] } = useQuery({
    queryKey: ['database-releases'],
    queryFn: databaseReleasesApi.getAll,
  })

  const { data: efforts = [] } = useQuery({
    queryKey: ['reporting-efforts'],
    queryFn: reportingEffortsApi.getAll,
  })

  const { data: trackers = [], isLoading } = useQuery({
    queryKey: ['trackers-all'],
    queryFn: trackerApi.getAll,
  })

  // Fetch milestones for the Gantt chart
  const { data: milestones = [] } = useQuery({
    queryKey: ['milestones-dashboard'],
    queryFn: () => milestonesApi.getForDashboard({ include_completed: true }),
  })

  // Build hierarchical data structure
  const hierarchicalData = useMemo(() => {
    // Group items by reporting effort
    const itemsByEffort = new Map<number, ReportingEffortItemTracker[]>()
    trackers.forEach(t => {
      const effortId = t.reporting_effort_id
      if (effortId === undefined) return
      if (!itemsByEffort.has(effortId)) {
        itemsByEffort.set(effortId, [])
      }
      itemsByEffort.get(effortId)!.push(t)
    })

    // Build study hierarchy
    return studies.map(study => {
      const studyReleases = releases.filter(r => r.study_id === study.id)
      const studyItems: ReportingEffortItemTracker[] = []
      let studyTrackerCount = 0

      const releaseData = studyReleases.map(release => {
        const releaseEfforts = efforts.filter(e => e.database_release_id === release.id)
        const releaseItems: ReportingEffortItemTracker[] = []
        let releaseTrackerCount = 0

        const effortData = releaseEfforts.map(effort => {
          const effortItems = itemsByEffort.get(effort.id) || []
          const trackerGroups = groupItemsIntoTrackers(effortItems)
          releaseItems.push(...effortItems)
          releaseTrackerCount += trackerGroups.length
          return {
            effort,
            items: effortItems,
            trackerGroups,
            trackerCount: trackerGroups.length,
            stats: calculateStats(effortItems),
          }
        })

        studyItems.push(...releaseItems)
        studyTrackerCount += releaseTrackerCount
        return {
          release,
          efforts: effortData,
          items: releaseItems,
          trackerCount: releaseTrackerCount,
          stats: calculateStats(releaseItems),
        }
      })

      return {
        study,
        releases: releaseData,
        items: studyItems,
        trackerCount: studyTrackerCount,
        stats: calculateStats(studyItems),
      }
    }).filter(s => s.items.length > 0) // Only show studies with items
  }, [studies, releases, efforts, trackers])

  // Overall stats - items and trackers
  const overallStats = useMemo(() => calculateStats(trackers), [trackers])
  const totalTrackerCount = useMemo(() =>
    hierarchicalData.reduce((sum, s) => sum + s.trackerCount, 0),
    [hierarchicalData]
  )

  const toggleStudy = (studyId: number) => {
    setExpandedStudies(prev => {
      const next = new Set(prev)
      if (next.has(studyId)) {
        next.delete(studyId)
      } else {
        next.add(studyId)
      }
      return next
    })
  }

  const toggleRelease = (releaseId: number) => {
    setExpandedReleases(prev => {
      const next = new Set(prev)
      if (next.has(releaseId)) {
        next.delete(releaseId)
      } else {
        next.add(releaseId)
      }
      return next
    })
  }

  const expandAll = () => {
    setExpandedStudies(new Set(hierarchicalData.map(s => s.study.id)))
    setExpandedReleases(new Set(hierarchicalData.flatMap(s => s.releases.map(r => r.release.id))))
  }

  const collapseAll = () => {
    setExpandedStudies(new Set())
    setExpandedReleases(new Set())
  }

  if (isLoading) {
    return <PageLoader text="Loading dashboard..." />
  }

  return (
    <div className="space-y-6">
      {/* Overview Summary */}
      <div className="grid gap-4 md:grid-cols-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-primary">{hierarchicalData.length}</p>
            <p className="text-sm text-muted-foreground">Active Studies</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-primary">
              {hierarchicalData.reduce((sum, s) => sum + s.releases.length, 0)}
            </p>
            <p className="text-sm text-muted-foreground">DB Releases</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-primary">
              {hierarchicalData.reduce((sum, s) => sum + s.releases.reduce((rs, r) => rs + r.efforts.length, 0), 0)}
            </p>
            <p className="text-sm text-muted-foreground">Reporting Efforts</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-primary">{totalTrackerCount}</p>
            <p className="text-sm text-muted-foreground">Total Trackers</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-primary">{overallStats.total}</p>
            <p className="text-sm text-muted-foreground">Total Items</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-3xl font-bold text-green-500">
              {overallStats.total > 0 ? Math.round((overallStats.completed / overallStats.total) * 100) : 0}%
            </p>
            <p className="text-sm text-muted-foreground">Items Completed</p>
          </CardContent>
        </Card>
      </div>

      {/* Overall Progress */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Overall Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ProgressBar stats={overallStats} showLabels />
        </CardContent>
      </Card>

      {/* Milestone Timeline */}
      {milestones.length > 0 && (
        <MilestoneGantt
          milestones={milestones}
          title="Project Milestones Timeline"
          showLegend={true}
          height={Math.min(400, Math.max(200, milestones.length * 30 + 80))}
        />
      )}

      {hierarchicalData.length === 0 ? (
        <EmptyState
          icon={BarChart3}
          title="No tracker data available"
          description="Add reporting efforts and tracker items to see progress analytics."
        />
      ) : (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FolderOpen className="h-5 w-5" />
                Progress by Study
              </CardTitle>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={expandAll}>
                  Expand All
                </Button>
                <Button variant="outline" size="sm" onClick={collapseAll}>
                  Collapse All
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {hierarchicalData.map(({ study, releases, stats }) => (
              <div key={study.id} className="border rounded-lg">
                {/* Study Row */}
                <div
                  className="flex items-center gap-3 p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => toggleStudy(study.id)}
                >
                  <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0">
                    {expandedStudies.has(study.id) ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </Button>
                  <FolderOpen className="h-5 w-5 text-primary shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold truncate">{study.study_label}</span>
                      <CompletionBadge stats={stats} />
                      <span className="text-sm text-muted-foreground">
                        ({stats.total} items)
                      </span>
                    </div>
                    <ProgressBar stats={stats} />
                  </div>
                </div>

                {/* Database Releases */}
                {expandedStudies.has(study.id) && releases.length > 0 && (
                  <div className="border-t bg-muted/20">
                    {releases.map(({ release, efforts, stats: releaseStats }) => (
                      <div key={release.id} className="border-b last:border-b-0">
                        {/* Release Row */}
                        <div
                          className="flex items-center gap-3 p-3 pl-10 cursor-pointer hover:bg-muted/50 transition-colors"
                          onClick={() => toggleRelease(release.id)}
                        >
                          <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0">
                            {expandedReleases.has(release.id) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </Button>
                          <Database className="h-4 w-4 text-blue-500 shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium truncate">
                                {release.database_release_label}
                              </span>
                              <CompletionBadge stats={releaseStats} />
                              <span className="text-sm text-muted-foreground">
                                ({releaseStats.total} items)
                              </span>
                            </div>
                            <ProgressBar stats={releaseStats} />
                          </div>
                        </div>

                        {/* Reporting Efforts */}
                        {expandedReleases.has(release.id) && efforts.length > 0 && (
                          <div className="bg-muted/30">
                            {efforts.map(({ effort, trackerGroups, trackerCount, stats: effortStats }) => (
                              <div key={effort.id} className="border-t border-muted">
                                <div className="flex items-center gap-3 p-3 pl-20">
                                  <FileText className="h-4 w-4 text-purple-500 shrink-0" />
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                      <span className="text-sm font-medium truncate">
                                        {effort.database_release_label}
                                      </span>
                                      <Badge variant="outline" className="text-xs">
                                        {trackerCount} trackers
                                      </Badge>
                                      <CompletionBadge stats={effortStats} />
                                      <span className="text-xs text-muted-foreground">
                                        ({effortStats.total} items)
                                      </span>
                                    </div>
                                    <ProgressBar stats={effortStats} />
                                  </div>
                                </div>
                                {/* Tracker Groups (TLF, SDTM, ADAM) */}
                                <div className="pl-28 pb-2 space-y-1">
                                  {trackerGroups.map((group) => (
                                    <div
                                      key={group.type}
                                      className="flex items-center gap-2 text-xs text-muted-foreground"
                                    >
                                      <Badge
                                        variant="secondary"
                                        className={cn(
                                          'text-xs min-w-[50px] justify-center',
                                          group.type === 'TLF' && 'bg-blue-100 text-blue-700',
                                          group.type === 'SDTM' && 'bg-green-100 text-green-700',
                                          group.type === 'ADAM' && 'bg-purple-100 text-purple-700'
                                        )}
                                      >
                                        {group.type}
                                      </Badge>
                                      <span>{group.items.length} items</span>
                                      <span className="text-muted-foreground/60">•</span>
                                      <span className="text-green-600">
                                        {group.stats.completed} done
                                      </span>
                                      {group.stats.in_progress > 0 && (
                                        <>
                                          <span className="text-muted-foreground/60">•</span>
                                          <span className="text-blue-600">
                                            {group.stats.in_progress} in progress
                                          </span>
                                        </>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Status Legend */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Status Legend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            {Object.entries(STATUS_CONFIG).map(([key, config]) => {
              const Icon = config.icon
              return (
                <div key={key} className="flex items-center gap-2">
                  <div className={cn('h-3 w-3 rounded-full', config.color)} />
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{config.label}</span>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
