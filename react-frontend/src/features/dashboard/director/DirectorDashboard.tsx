/**
 * Director Dashboard
 * 
 * Strategic overview for programming team directors including:
 * - Warning banner for critical issues
 * - Portfolio health overview
 * - Team utilization
 * - Velocity trends
 * - Capacity forecasting
 */

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useState } from 'react'
import { WarningBanner } from './WarningBanner'
import { PortfolioHealthTable } from './PortfolioHealthTable'
import { VelocityTrendChart } from './VelocityTrendChart'
import { TeamUtilizationChart } from './TeamUtilizationChart'
import { CapacityForecastChart } from './CapacityForecastChart'
import { EntityOverviewCharts } from './EntityOverviewCharts'
import {
  getPortfolioHealth,
  getTeamUtilization,
  getDashboardWarnings,
  getCapacityForecast,
  getStudyVelocity,
  getQCMetrics,
  getEntityOverview,
} from '@/api/endpoints/analytics'

export function DirectorDashboard() {
  const [selectedStudyId, setSelectedStudyId] = useState<number | null>(null)
  const [velocityWeeks, setVelocityWeeks] = useState(12)

  // Fetch portfolio health
  const { data: portfolioHealth, isLoading: isLoadingHealth } = useQuery({
    queryKey: ['portfolioHealth'],
    queryFn: getPortfolioHealth,
    refetchInterval: 60000, // Refresh every minute
  })

  // Fetch dashboard warnings
  const { data: warnings, isLoading: isLoadingWarnings } = useQuery({
    queryKey: ['dashboardWarnings'],
    queryFn: () => getDashboardWarnings(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Fetch team utilization
  const { data: utilization, isLoading: isLoadingUtilization } = useQuery({
    queryKey: ['teamUtilization'],
    queryFn: getTeamUtilization,
    refetchInterval: 60000,
  })

  // Fetch capacity forecast
  const { data: forecast, isLoading: isLoadingForecast } = useQuery({
    queryKey: ['capacityForecast'],
    queryFn: () => getCapacityForecast(8),
    refetchInterval: 120000,
  })

  // Fetch velocity for selected study
  const { data: velocity, isLoading: isLoadingVelocity } = useQuery({
    queryKey: ['studyVelocity', selectedStudyId, velocityWeeks],
    queryFn: () => selectedStudyId ? getStudyVelocity(selectedStudyId, velocityWeeks) : null,
    enabled: !!selectedStudyId,
  })

  // Fetch QC metrics
  const { data: qcMetrics } = useQuery({
    queryKey: ['qcMetrics'],
    queryFn: () => getQCMetrics(undefined, 30),
    refetchInterval: 60000,
  })

  // Fetch entity overview
  const { data: entityOverview, isLoading: isLoadingEntityOverview } = useQuery({
    queryKey: ['entityOverview'],
    queryFn: getEntityOverview,
    refetchInterval: 60000,
  })

  // Get summary stats
  const totalStudies = portfolioHealth?.studies.length || 0
  const atRiskStudies = portfolioHealth?.summary.at_risk || 0
  const totalTeamMembers = utilization?.members.length || 0

  return (
    <div className="space-y-6 p-4">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Director Dashboard
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Strategic overview of programming team and portfolio health
          </p>
        </div>
        <div className="text-right text-sm text-gray-500">
          {portfolioHealth?.generated_at && (
            <span>
              Last updated: {new Date(portfolioHealth.generated_at).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Warning Banner */}
      <WarningBanner warnings={warnings ?? null} isLoading={isLoadingWarnings} />

      {/* Entity Overview Charts */}
      <EntityOverviewCharts data={entityOverview ?? null} isLoading={isLoadingEntityOverview} />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-indigo-600">{totalStudies}</div>
            <div className="text-sm text-gray-500">Active Studies</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className={`text-2xl font-bold ${atRiskStudies > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
              {atRiskStudies}
            </div>
            <div className="text-sm text-gray-500">At Risk</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-indigo-600">{totalTeamMembers}</div>
            <div className="text-sm text-gray-500">Team Members</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold text-emerald-600">
              {qcMetrics?.first_pass_rate_percentage.toFixed(0) || '--'}%
            </div>
            <div className="text-sm text-gray-500">QC First Pass Rate</div>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Portfolio Health */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Portfolio Health</CardTitle>
          </CardHeader>
          <CardContent>
            <PortfolioHealthTable 
              studies={portfolioHealth?.studies || []} 
              isLoading={isLoadingHealth} 
            />
          </CardContent>
        </Card>

        {/* Team Utilization */}
        <TeamUtilizationChart 
          members={utilization?.members || []} 
          isLoading={isLoadingUtilization} 
        />

        {/* Capacity Forecast */}
        <CapacityForecastChart 
          weeks={forecast?.weeks || []} 
          isLoading={isLoadingForecast} 
        />

        {/* Velocity Trend - with study selector */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Velocity Trend</CardTitle>
              <div className="flex gap-2">
                <Select
                  value={selectedStudyId?.toString() || ''}
                  onValueChange={(v) => setSelectedStudyId(v ? parseInt(v) : null)}
                >
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Select a study" />
                  </SelectTrigger>
                  <SelectContent>
                    {portfolioHealth?.studies.map((study) => (
                      <SelectItem key={study.study_id} value={study.study_id.toString()}>
                        {study.study_label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select
                  value={velocityWeeks.toString()}
                  onValueChange={(v) => setVelocityWeeks(parseInt(v))}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="4">4 weeks</SelectItem>
                    <SelectItem value="8">8 weeks</SelectItem>
                    <SelectItem value="12">12 weeks</SelectItem>
                    <SelectItem value="24">24 weeks</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {selectedStudyId ? (
              <VelocityTrendChart
                data={velocity?.weekly_data || []}
                avgPointsPerWeek={velocity?.avg_points_per_week || 0}
                isLoading={isLoadingVelocity}
              />
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500 bg-gray-50 dark:bg-gray-900 rounded-lg">
                Select a study to view velocity trend
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

