/**
 * Analytics API endpoints for Director Dashboard
 */

import { apiClient } from '../client'
import type {
  PortfolioHealthResponse,
  StudyVelocityResponse,
  TeamUtilizationResponse,
  DashboardWarnings,
  TeamCapacityResponse,
  CapacityForecastResponse,
  QCMetricsResponse,
  MilestoneEstimateResponse,
} from '../../types/analytics'

const BASE_URL = '/api/v1/analytics'

/**
 * Get portfolio health status for all studies
 */
export const getPortfolioHealth = async (): Promise<PortfolioHealthResponse> => {
  const response = await apiClient.get<PortfolioHealthResponse>(`${BASE_URL}/portfolio-health`)
  return response.data
}

/**
 * Get velocity trend for a study
 */
export const getStudyVelocity = async (
  studyId: number,
  weeks = 12
): Promise<StudyVelocityResponse> => {
  const response = await apiClient.get<StudyVelocityResponse>(
    `${BASE_URL}/velocity/study/${studyId}`,
    { params: { weeks } }
  )
  return response.data
}

/**
 * Get velocity for a user
 */
export const getUserVelocity = async (
  userId: number,
  studyId?: number,
  weeks = 8
) => {
  const response = await apiClient.get(`${BASE_URL}/velocity/user/${userId}`, {
    params: { study_id: studyId, weeks },
  })
  return response.data
}

/**
 * Get team utilization across all studies
 */
export const getTeamUtilization = async (): Promise<TeamUtilizationResponse> => {
  const response = await apiClient.get<TeamUtilizationResponse>(`${BASE_URL}/team-utilization`)
  return response.data
}

/**
 * Get all dashboard warnings
 */
export const getDashboardWarnings = async (
  studyId?: number
): Promise<DashboardWarnings> => {
  const response = await apiClient.get<DashboardWarnings>(`${BASE_URL}/warnings`, {
    params: { study_id: studyId },
  })
  return response.data
}

/**
 * Get team capacity for a study
 */
export const getTeamCapacity = async (studyId: number): Promise<TeamCapacityResponse> => {
  const response = await apiClient.get<TeamCapacityResponse>(`${BASE_URL}/capacity/study/${studyId}`)
  return response.data
}

/**
 * Get capacity forecast for upcoming weeks
 */
export const getCapacityForecast = async (
  weeks = 8
): Promise<CapacityForecastResponse> => {
  const response = await apiClient.get<CapacityForecastResponse>(`${BASE_URL}/capacity-forecast`, {
    params: { weeks },
  })
  return response.data
}

/**
 * Get QC metrics
 */
export const getQCMetrics = async (
  studyId?: number,
  days = 30
): Promise<QCMetricsResponse> => {
  const response = await apiClient.get<QCMetricsResponse>(`${BASE_URL}/qc-metrics`, {
    params: { study_id: studyId, days },
  })
  return response.data
}

/**
 * Get milestone due date estimate
 */
export const getMilestoneEstimate = async (
  milestoneId: number
): Promise<MilestoneEstimateResponse> => {
  const response = await apiClient.get<MilestoneEstimateResponse>(
    `${BASE_URL}/milestone/${milestoneId}/estimate`
  )
  return response.data
}

