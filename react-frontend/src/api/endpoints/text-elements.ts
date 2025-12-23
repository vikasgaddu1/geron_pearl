import { apiClient } from '../client'
import type { TextElement, TextElementFormData } from '@/types'

const BASE_PATH = '/api/v1/text-elements'

export const textElementsApi = {
  getAll: async (): Promise<TextElement[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`)
    return response.data
  },

  getById: async (id: number): Promise<TextElement> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  getByType: async (type: string): Promise<TextElement[]> => {
    const response = await apiClient.get(`${BASE_PATH}/?type=${type}`)
    return response.data
  },

  create: async (data: TextElementFormData): Promise<TextElement> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  update: async (id: number, data: TextElementFormData): Promise<TextElement> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },
}

