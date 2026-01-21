import { apiClient } from '../client'
import type { FeatureRequest, FeatureRequestCreate } from '@/types'

const BASE_PATH = '/api/v1/feedback'

export const feedbackApi = {
  /**
   * Submit a new feature request or bug report
   */
  submit: async (data: FeatureRequestCreate): Promise<FeatureRequest> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  /**
   * Get all feedback submitted by the current user
   */
  getMyRequests: async (skip = 0, limit = 50): Promise<FeatureRequest[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`, {
      params: { skip, limit }
    })
    return response.data
  },

  /**
   * Get detail of a specific feedback submission
   */
  getRequest: async (feedbackId: number): Promise<FeatureRequest> => {
    const response = await apiClient.get(`${BASE_PATH}/${feedbackId}`)
    return response.data
  },
}
