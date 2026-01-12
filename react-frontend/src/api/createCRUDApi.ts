/**
 * Factory function to create standard CRUD API endpoints
 * Reduces boilerplate for entities with common CRUD patterns
 */
import { apiClient } from './client'

export interface CRUDApi<T, TCreate = Partial<T>, TUpdate = Partial<T>> {
  getAll: () => Promise<T[]>
  getById: (id: number) => Promise<T>
  create: (data: TCreate) => Promise<T>
  update: (id: number, data: TUpdate) => Promise<T>
  delete: (id: number) => Promise<void>
}

/**
 * Creates a standard CRUD API for an entity
 * @param basePath - The API base path (e.g., '/api/v1/packages')
 * @returns Object with getAll, getById, create, update, delete methods
 *
 * @example
 * const packagesApi = createCRUDApi<Package, PackageFormData>('/api/v1/packages')
 *
 * // Can be extended with custom methods:
 * const extendedApi = {
 *   ...createCRUDApi<Package, PackageFormData>('/api/v1/packages'),
 *   getItems: async (packageId: number) => { ... }
 * }
 */
export function createCRUDApi<T, TCreate = Partial<T>, TUpdate = TCreate>(
  basePath: string
): CRUDApi<T, TCreate, TUpdate> {
  return {
    getAll: async (): Promise<T[]> => {
      const response = await apiClient.get(`${basePath}/`)
      return response.data
    },

    getById: async (id: number): Promise<T> => {
      const response = await apiClient.get(`${basePath}/${id}`)
      return response.data
    },

    create: async (data: TCreate): Promise<T> => {
      const response = await apiClient.post(`${basePath}/`, data)
      return response.data
    },

    update: async (id: number, data: TUpdate): Promise<T> => {
      const response = await apiClient.put(`${basePath}/${id}`, data)
      return response.data
    },

    delete: async (id: number): Promise<void> => {
      await apiClient.delete(`${basePath}/${id}`)
    },
  }
}

/**
 * Creates a CRUD API with parent-scoped getAll
 * Useful for nested resources (e.g., items within a package)
 */
export function createNestedCRUDApi<T, TCreate = Partial<T>, TUpdate = TCreate>(
  parentPath: string,
  childPath: string
) {
  return {
    getAll: async (parentId: number): Promise<T[]> => {
      const response = await apiClient.get(`${parentPath}/${parentId}/${childPath}`)
      return response.data
    },

    getById: async (id: number): Promise<T> => {
      const response = await apiClient.get(`${parentPath}/${childPath}/${id}`)
      return response.data
    },

    create: async (parentId: number, data: TCreate): Promise<T> => {
      const response = await apiClient.post(`${parentPath}/${parentId}/${childPath}`, data)
      return response.data
    },

    update: async (id: number, data: TUpdate): Promise<T> => {
      const response = await apiClient.put(`${parentPath}/${childPath}/${id}`, data)
      return response.data
    },

    delete: async (id: number): Promise<void> => {
      await apiClient.delete(`${parentPath}/${childPath}/${id}`)
    },
  }
}
