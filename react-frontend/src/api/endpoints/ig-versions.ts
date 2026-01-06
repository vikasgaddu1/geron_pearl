import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '../client'
import type { IGVersion } from '@/types'

const BASE_PATH = '/api/v1/ig-versions'

export interface IGVersionCreate {
  standard_type: 'SDTM' | 'ADaM'
  version: string
  description?: string
  is_active?: boolean
}

export interface IGVersionUpdate {
  standard_type?: 'SDTM' | 'ADaM'
  version?: string
  description?: string
  is_active?: boolean
}

export const igVersionsApi = {
  getAll: async (params?: { standard_type?: string; active_only?: boolean }): Promise<IGVersion[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`, { params })
    return response.data
  },

  get: async (id: number): Promise<IGVersion> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  create: async (data: IGVersionCreate): Promise<IGVersion> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  update: async (id: number, data: IGVersionUpdate): Promise<IGVersion> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },
}

// Query keys
export const igVersionKeys = {
  all: ['ig-versions'] as const,
  lists: () => [...igVersionKeys.all, 'list'] as const,
  list: (filters: { standard_type?: string; active_only?: boolean }) => 
    [...igVersionKeys.lists(), filters] as const,
  details: () => [...igVersionKeys.all, 'detail'] as const,
  detail: (id: number) => [...igVersionKeys.details(), id] as const,
}

// Hook to get all IG versions
export function useIGVersions(params?: { standard_type?: string; active_only?: boolean }) {
  return useQuery({
    queryKey: igVersionKeys.list(params || {}),
    queryFn: () => igVersionsApi.getAll(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Hook to get IG versions by standard type
export function useIGVersionsByType(standardType: 'SDTM' | 'ADaM', activeOnly = true) {
  return useQuery({
    queryKey: igVersionKeys.list({ standard_type: standardType, active_only: activeOnly }),
    queryFn: () => igVersionsApi.getAll({ standard_type: standardType, active_only: activeOnly }),
    staleTime: 5 * 60 * 1000,
  })
}

// Hook to create IG version
export function useCreateIGVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: igVersionsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: igVersionKeys.all })
    },
  })
}

// Hook to update IG version
export function useUpdateIGVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: IGVersionUpdate }) => 
      igVersionsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: igVersionKeys.all })
    },
  })
}

// Hook to delete IG version
export function useDeleteIGVersion() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: igVersionsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: igVersionKeys.all })
    },
  })
}

