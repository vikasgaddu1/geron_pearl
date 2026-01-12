/**
 * Entity Overview Charts component
 *
 * Shows use case assignments with study, db release, and reporting effort names
 */

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
import type { EntityOverviewResponse } from '@/types/analytics'

interface EntityOverviewChartsProps {
  data: EntityOverviewResponse | null
  isLoading?: boolean
}

// Colors for use case badges
const BADGE_COLORS = [
  'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200',
  'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200',
  'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  'bg-rose-100 text-rose-800 dark:bg-rose-900 dark:text-rose-200',
  'bg-violet-100 text-violet-800 dark:bg-violet-900 dark:text-violet-200',
  'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
  'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200',
  'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
]

export function EntityOverviewCharts({ data, isLoading = false }: EntityOverviewChartsProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Use Case Assignments</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 bg-gray-100 dark:bg-gray-800 animate-pulse rounded" />
        </CardContent>
      </Card>
    )
  }

  // Filter use cases that have combinations
  const usecasesWithData = (data?.usecase_breakdown || []).filter(
    uc => uc.combinations && uc.combinations.length > 0
  )

  if (usecasesWithData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Use Case Assignments</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-32 flex items-center justify-center text-gray-500">
            No use case assignments available
          </div>
        </CardContent>
      </Card>
    )
  }

  // Create a color map for use cases
  const usecaseColorMap = new Map<string, string>()
  usecasesWithData.forEach((uc, index) => {
    usecaseColorMap.set(uc.usecase_name, BADGE_COLORS[index % BADGE_COLORS.length])
  })

  // Flatten data for table view - one row per combination
  const tableData = usecasesWithData.flatMap(uc =>
    uc.combinations.map(combo => ({
      usecase_name: uc.usecase_name,
      study_label: combo.study_label,
      db_release_name: combo.db_release_name,
      reporting_effort_id: combo.reporting_effort_id,
      reporting_effort_name: combo.reporting_effort_name,
      badgeColor: usecaseColorMap.get(uc.usecase_name) || BADGE_COLORS[0],
    }))
  )

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Use Case Assignments</CardTitle>
        <p className="text-sm text-muted-foreground">
          Reporting efforts assigned to each use case
        </p>
      </CardHeader>
      <CardContent>
        <div className="max-h-80 overflow-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[150px]">Use Case</TableHead>
                <TableHead>Study</TableHead>
                <TableHead>DB Release</TableHead>
                <TableHead>Reporting Effort</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tableData.map((row) => (
                <TableRow key={`${row.usecase_name}-${row.reporting_effort_id}`}>
                  <TableCell>
                    <Badge variant="secondary" className={row.badgeColor}>
                      {row.usecase_name}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-medium">{row.study_label}</TableCell>
                  <TableCell>{row.db_release_name}</TableCell>
                  <TableCell>
                    <span title={`ID: ${row.reporting_effort_id}`}>
                      {row.reporting_effort_name}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        {/* Summary */}
        <div className="mt-4 pt-4 border-t flex gap-4 text-sm text-muted-foreground">
          <span>{usecasesWithData.length} use cases</span>
          <span>•</span>
          <span>{tableData.length} assignments</span>
        </div>
      </CardContent>
    </Card>
  )
}
