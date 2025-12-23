import { apiClient } from '../client'
import type { TrackerTag, TrackerTagSummary } from '@/types'

const BASE_PATH = '/api/v1/tracker-tags'

export interface TrackerTagCreate {
  name: string
  color: string
  description?: string
}

export interface TrackerTagUpdate {
  name?: string
  color?: string
  description?: string
}

export interface BulkTagAssignment {
  tracker_ids: number[]
  tag_id: number
}

export interface BulkOperationResult {
  success: boolean
  affected_count: number
  errors: string[]
}

export const trackerTagsApi = {
  // Tag Management
  getAll: async (): Promise<TrackerTag[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`)
    return response.data
  },

  getById: async (id: number): Promise<TrackerTag> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  create: async (data: TrackerTagCreate): Promise<TrackerTag> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  update: async (id: number, data: TrackerTagUpdate): Promise<TrackerTag> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },

  // Tag Assignment
  assignTag: async (trackerId: number, tagId: number): Promise<void> => {
    await apiClient.post(`${BASE_PATH}/assign`, {
      tracker_id: trackerId,
      tag_id: tagId
    })
  },

  removeTag: async (trackerId: number, tagId: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/assign/${trackerId}/${tagId}`)
  },

  getTrackerTags: async (trackerId: number): Promise<TrackerTagSummary[]> => {
    const response = await apiClient.get(`${BASE_PATH}/tracker/${trackerId}`)
    return response.data
  },

  getTrackersByTag: async (tagId: number): Promise<number[]> => {
    const response = await apiClient.get(`${BASE_PATH}/by-tag/${tagId}/trackers`)
    return response.data
  },

  // Bulk Operations
  bulkAssign: async (data: BulkTagAssignment): Promise<BulkOperationResult> => {
    const response = await apiClient.post(`${BASE_PATH}/bulk-assign`, data)
    return response.data
  },

  bulkRemove: async (data: BulkTagAssignment): Promise<BulkOperationResult> => {
    const response = await apiClient.post(`${BASE_PATH}/bulk-remove`, data)
    return response.data
  },

  getTagsForTrackersBulk: async (trackerIds: number[]): Promise<Record<number, TrackerTagSummary[]>> => {
    const response = await apiClient.post(`${BASE_PATH}/bulk-get`, trackerIds)
    return response.data
  }
}

