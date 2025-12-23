import { apiClient } from '../client'
import type { DatabaseRelease, DatabaseReleaseFormData } from '@/types'

const BASE_PATH = '/api/v1/database-releases'

export const databaseReleasesApi = {
  getAll: async (): Promise<DatabaseRelease[]> => {
    const response = await apiClient.get(BASE_PATH)
    return response.data
  },

  getById: async (id: number): Promise<DatabaseRelease> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  getByStudyId: async (studyId: number): Promise<DatabaseRelease[]> => {
    const response = await apiClient.get(`${BASE_PATH}?study_id=${studyId}`)
    return response.data
  },

  create: async (data: DatabaseReleaseFormData): Promise<DatabaseRelease> => {
    const response = await apiClient.post(BASE_PATH, data)
    return response.data
  },

  update: async (id: number, data: DatabaseReleaseFormData): Promise<DatabaseRelease> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },
}

