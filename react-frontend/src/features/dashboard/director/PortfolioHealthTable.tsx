/**
 * Portfolio Health Table component
 * 
 * Shows health status for all studies with:
 * - Progress (items and complexity)
 * - Risk indicators
 * - Team capacity
 */

import { useMemo } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import type { StudyHealthStatus } from '@/types/analytics'

interface PortfolioHealthTableProps {
  studies: StudyHealthStatus[]
  isLoading: boolean
}

const getRiskBadge = (risk: string) => {
  switch (risk) {
    case 'low':
      return <Badge className="bg-emerald-500 hover:bg-emerald-600">Low Risk</Badge>
    case 'medium':
      return <Badge className="bg-amber-500 hover:bg-amber-600">Medium Risk</Badge>
    case 'high':
      return <Badge className="bg-red-500 hover:bg-red-600">High Risk</Badge>
    default:
      return <Badge variant="secondary">{risk}</Badge>
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'on_track':
      return <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">On Track</Badge>
    case 'in_progress':
      return <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">In Progress</Badge>
    case 'at_risk':
      return <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">At Risk</Badge>
    case 'not_started':
      return <Badge className="bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200">Not Started</Badge>
    default:
      return <Badge variant="outline">{status}</Badge>
  }
}

export function PortfolioHealthTable({ studies, isLoading }: PortfolioHealthTableProps) {
  const sortedStudies = useMemo(() => {
    // Sort by risk (high first), then by progress (lowest first)
    return [...studies].sort((a, b) => {
      const riskOrder = { high: 0, medium: 1, low: 2 }
      const riskDiff = (riskOrder[a.risk] ?? 3) - (riskOrder[b.risk] ?? 3)
      if (riskDiff !== 0) return riskDiff
      return a.progress_percentage - b.progress_percentage
    })
  }, [studies])

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-12 bg-gray-100 dark:bg-gray-800 animate-pulse rounded" />
        ))}
      </div>
    )
  }

  if (studies.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No studies found
      </div>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Study</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Risk</TableHead>
            <TableHead className="text-center">Progress</TableHead>
            <TableHead className="text-center">Items</TableHead>
            <TableHead className="text-center">Complexity</TableHead>
            <TableHead className="text-center">Team</TableHead>
            <TableHead className="text-right">Velocity</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedStudies.map((study) => (
            <TableRow key={study.study_id} className="hover:bg-gray-50 dark:hover:bg-gray-900">
              <TableCell className="font-medium">{study.study_label}</TableCell>
              <TableCell>{getStatusBadge(study.status)}</TableCell>
              <TableCell>{getRiskBadge(study.risk)}</TableCell>
              <TableCell className="w-40">
                <div className="flex items-center gap-2">
                  <Progress value={study.progress_percentage} className="h-2" />
                  <span className="text-sm text-gray-500 w-12 text-right">
                    {study.progress_percentage.toFixed(0)}%
                  </span>
                </div>
              </TableCell>
              <TableCell className="text-center">
                <span className="font-mono text-sm">
                  {study.completed_items}/{study.total_items}
                </span>
              </TableCell>
              <TableCell className="text-center">
                <span className="font-mono text-sm">
                  {study.completed_complexity}/{study.total_complexity}
                </span>
              </TableCell>
              <TableCell className="text-center">
                <span className="text-sm">{study.team_size} members</span>
              </TableCell>
              <TableCell className="text-right">
                <span className="font-mono text-sm">
                  {study.team_capacity_points_per_week.toFixed(1)} pts/wk
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

