import { apiClient } from '../client'
import type {
  Study,
  StudyFormData,
  StudyMembersResponse,
  StudyPermissions,
  UserStudyRole,
  AssignStudyRoleRequest,
  StudyRole,
  BulkHierarchyRow,
  BulkHierarchyResponse,
  StudyResponsibleUser,
  StudyResponsibleUsersResponse,
  AssignResponsibleUserRequest,
  UpdateResponsibleUserRequest,
  StudyDefaultBiostat,
  StudyBiostatUser,
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

  bulkHierarchyUpload: async (rows: BulkHierarchyRow[]): Promise<BulkHierarchyResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/bulk-hierarchy`, rows)
    return response.data
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
   * Remove a user's explicit role from a study
   */
  removeMember: async (studyId: number, userId: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${studyId}/members/${userId}`)
  },

  /**
   * Get users available for study role assignment (requires responsible user or ADMIN)
   * Returns non-admin, active users from the same tenant
   */
  getAvailableUsers: async (studyId: number): Promise<{ id: number; username: string; email?: string; is_admin: boolean; is_active: boolean }[]> => {
    const response = await apiClient.get(`${BASE_PATH}/${studyId}/available-users`)
    return response.data
  },

  // ==================== Study Responsible Users Management ====================

  /**
   * Get all responsible users for a study
   */
  getResponsibleUsers: async (studyId: number): Promise<StudyResponsibleUsersResponse> => {
    const response = await apiClient.get(`${BASE_PATH}/${studyId}/responsible-users`)
    return response.data
  },

  /**
   * Assign a user as responsible for a study
   */
  assignResponsibleUser: async (studyId: number, data: AssignResponsibleUserRequest): Promise<StudyResponsibleUser> => {
    const response = await apiClient.post(`${BASE_PATH}/${studyId}/responsible-users`, data)
    return response.data
  },

  /**
   * Update a responsible user's status (e.g., set as primary)
   */
  updateResponsibleUser: async (studyId: number, userId: number, data: UpdateResponsibleUserRequest): Promise<StudyResponsibleUser> => {
    const response = await apiClient.put(`${BASE_PATH}/${studyId}/responsible-users/${userId}`, data)
    return response.data
  },

  /**
   * Remove a user's responsible status from a study
   */
  removeResponsibleUser: async (studyId: number, userId: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${studyId}/responsible-users/${userId}`)
  },

  // ==================== Study Default Biostat Management ====================

  /**
   * Get the default biostat reviewer for a study
   */
  getDefaultBiostat: async (studyId: number): Promise<StudyDefaultBiostat | null> => {
    const response = await apiClient.get(`${BASE_PATH}/${studyId}/default-biostat`)
    return response.data
  },

  /**
   * Set the default biostat reviewer for a study
   */
  setDefaultBiostat: async (studyId: number, userId: number): Promise<StudyDefaultBiostat> => {
    const response = await apiClient.put(`${BASE_PATH}/${studyId}/default-biostat?user_id=${userId}`)
    return response.data
  },

  /**
   * Remove the default biostat reviewer from a study
   */
  removeDefaultBiostat: async (studyId: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${studyId}/default-biostat`)
  },

  /**
   * Get all users with BIOSTAT role for a study
   */
  getBiostatUsers: async (studyId: number): Promise<StudyBiostatUser[]> => {
    const response = await apiClient.get(`${BASE_PATH}/${studyId}/biostat-users`)
    return response.data
  },
}





