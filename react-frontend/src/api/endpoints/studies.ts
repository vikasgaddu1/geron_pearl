import { apiClient } from '../client'
import type { 
  Study, 
  StudyFormData, 
  StudyMembersResponse, 
  StudyPermissions, 
  UserStudyRole,
  AssignStudyRoleRequest,
  StudyRole
} from '@/types'

const BASE_PATH = '/api/v1/studies'

export const studiesApi = {
  getAll: async (): Promise<Study[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`)
    return response.data
  },

  getById: async (id: number): Promise<Study> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  create: async (data: StudyFormData): Promise<Study> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  update: async (id: number, data: StudyFormData): Promise<Study> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },

  // ==================== Study Member Management ====================

  /**
   * Get current user's permissions for a specific study
   */
  getMyPermissions: async (studyId: number): Promise<StudyPermissions> => {
    const response = await apiClient.get(`${BASE_PATH}/${studyId}/permissions`)
    return response.data
  },

  /**
   * Get all members for a study (requires LEAD or ADMIN)
   */
  getMembers: async (studyId: number, includeDefaults: boolean = true): Promise<StudyMembersResponse> => {
    const response = await apiClient.get(`${BASE_PATH}/${studyId}/members`, {
      params: { include_defaults: includeDefaults }
    })
    return response.data
  },

  /**
   * Assign or update a user's role in a study (requires LEAD or ADMIN)
   */
  assignMember: async (studyId: number, data: AssignStudyRoleRequest): Promise<UserStudyRole> => {
    const response = await apiClient.post(`${BASE_PATH}/${studyId}/members`, data)
    return response.data
  },

  /**
   * Update a user's role in a study (requires LEAD or ADMIN)
   */
  updateMemberRole: async (studyId: number, userId: number, role: StudyRole): Promise<UserStudyRole> => {
    const response = await apiClient.put(`${BASE_PATH}/${studyId}/members/${userId}`, { role })
    return response.data
  },

  /**
   * Remove a user's explicit role from a study (reverts to default viewer)
   */
  removeMember: async (studyId: number, userId: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${studyId}/members/${userId}`)
  },
}





