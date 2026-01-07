/**
 * Team Assignment API endpoints
 */

import api from '../api'
import type {
  StudyTeamAssignment,
  StudyTeamResponse,
  CreateTeamAssignmentRequest,
  ChangeAllocationRequest,
  EndAssignmentRequest,
  AllocationHistoryResponse,
} from '@/types/teamAssignment'

const BASE_URL = '/team-assignments'

/**
 * Get team members for a study
 */
export const getStudyTeam = async (studyId: number): Promise<StudyTeamResponse> => {
  const response = await api.get<StudyTeamResponse>(`${BASE_URL}/study/${studyId}`)
  return response.data
}

/**
 * Add a new team member to a study
 */
export const addTeamMember = async (
  studyId: number,
  data: CreateTeamAssignmentRequest
): Promise<StudyTeamAssignment> => {
  const response = await api.post<StudyTeamAssignment>(`${BASE_URL}/study/${studyId}`, data)
  return response.data
}

/**
 * Change a team member's allocation
 */
export const changeAllocation = async (
  assignmentId: number,
  data: ChangeAllocationRequest
): Promise<StudyTeamAssignment> => {
  const response = await api.post<StudyTeamAssignment>(
    `${BASE_URL}/${assignmentId}/change-allocation`,
    data
  )
  return response.data
}

/**
 * End a team member's assignment
 */
export const endAssignment = async (
  assignmentId: number,
  data: EndAssignmentRequest
): Promise<StudyTeamAssignment> => {
  const response = await api.post<StudyTeamAssignment>(
    `${BASE_URL}/${assignmentId}/end`,
    data
  )
  return response.data
}

/**
 * Get allocation history for a user on a study
 */
export const getAllocationHistory = async (
  userId: number,
  studyId: number
): Promise<AllocationHistoryResponse> => {
  const response = await api.get<AllocationHistoryResponse>(
    `${BASE_URL}/history/${userId}/${studyId}`
  )
  return response.data
}

/**
 * Get a single assignment
 */
export const getAssignment = async (assignmentId: number): Promise<StudyTeamAssignment> => {
  const response = await api.get<StudyTeamAssignment>(`${BASE_URL}/${assignmentId}`)
  return response.data
}

/**
 * Delete an assignment
 */
export const deleteAssignment = async (assignmentId: number): Promise<void> => {
  await api.delete(`${BASE_URL}/${assignmentId}`)
}

/**
 * Get orphaned items warnings
 */
export const getOrphanedItemsWarnings = async (studyId?: number) => {
  const response = await api.get(`${BASE_URL}/warnings/orphaned-items`, {
    params: { study_id: studyId },
  })
  return response.data
}

/**
 * Get over-allocated users warnings
 */
export const getOverAllocatedUsers = async () => {
  const response = await api.get(`${BASE_URL}/warnings/over-allocated`)
  return response.data
}

