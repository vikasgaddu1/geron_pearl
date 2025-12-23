import { apiClient } from '../client'
import type { TrackerComment, CommentType } from '@/types'

const BASE_PATH = '/api/v1/tracker-comments'

export interface CommentSummary {
  tracker_id: number
  total_comments: number
  unresolved_count: number
  programming_comments: number
  biostat_comments: number
}

export interface CreateCommentData {
  tracker_id: number
  comment_text: string
  comment_type?: CommentType | 'programming' | 'biostat'
  parent_comment_id?: number | null
}

export const trackerCommentsApi = {
  getByTrackerId: async (trackerId: number): Promise<TrackerComment[]> => {
    const response = await apiClient.get(`${BASE_PATH}/tracker/${trackerId}`)
    return response.data
  },

  getThreaded: async (trackerId: number): Promise<TrackerComment[]> => {
    const response = await apiClient.get(`${BASE_PATH}/tracker/${trackerId}/threaded`)
    return response.data
  },

  create: async (data: CreateCommentData): Promise<TrackerComment> => {
    const response = await apiClient.post(BASE_PATH, data)
    return response.data
  },

  resolve: async (commentId: number): Promise<TrackerComment> => {
    const response = await apiClient.post(`${BASE_PATH}/${commentId}/resolve`, null)
    return response.data
  },

  getUnresolvedCount: async (trackerId: number): Promise<{ count: number }> => {
    const response = await apiClient.get(`${BASE_PATH}/tracker/${trackerId}/unresolved-count`)
    return response.data
  },

  getSummary: async (trackerId: number): Promise<CommentSummary> => {
    const response = await apiClient.get(`${BASE_PATH}/tracker/${trackerId}/summary`)
    return response.data
  },
}


