import { apiClient } from '../client'
import type { User, UserFormData } from '@/types'

const BASE_PATH = '/api/v1/users'

export const usersApi = {
  getAll: async (): Promise<User[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`)
    return response.data
  },

  getById: async (id: number): Promise<User> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  create: async (data: UserFormData): Promise<User> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  update: async (id: number, data: UserFormData): Promise<User> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },
}

