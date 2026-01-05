import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { AppSettings, AppSettingsUpdate } from '@/types'

const BASE_PATH = '/api/v1/settings'

export const settingsApi = {
  get: async (): Promise<AppSettings> => {
    const response = await apiClient.get(`${BASE_PATH}/`)
    return response.data
  },

  update: async (data: AppSettingsUpdate): Promise<AppSettings> => {
    const response = await apiClient.put(`${BASE_PATH}/`, data)
    return response.data
  },

  getDefaultDueDateOffset: async (): Promise<number> => {
    const response = await apiClient.get(`${BASE_PATH}/default-due-date-offset`)
    return response.data.value
  },
}

// Query keys
export const settingsKeys = {
  all: ['settings'] as const,
  detail: () => [...settingsKeys.all, 'detail'] as const,
  dueDateOffset: () => [...settingsKeys.all, 'dueDateOffset'] as const,
}

// Hook to get all settings
export function useAppSettings() {
  return useQuery({
    queryKey: settingsKeys.detail(),
    queryFn: settingsApi.get,
    staleTime: 5 * 60 * 1000, // 5 minutes - settings don't change often
    gcTime: 30 * 60 * 1000, // 30 minutes cache
  })
}

// Hook to get just the due date offset (for use in forms)
export function useDefaultDueDateOffset() {
  return useQuery({
    queryKey: settingsKeys.dueDateOffset(),
    queryFn: settingsApi.getDefaultDueDateOffset,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes cache
  })
}

// Hook to update settings
export function useUpdateSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: settingsApi.update,
    onSuccess: () => {
      // Invalidate all settings queries to refetch fresh data
      queryClient.invalidateQueries({ queryKey: settingsKeys.all })
    },
  })
}
