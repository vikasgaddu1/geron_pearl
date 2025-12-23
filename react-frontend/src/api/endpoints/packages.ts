import { apiClient } from '../client'
import type { 
  Package, 
  PackageFormData, 
  PackageItem,
  PackageItemCreateWithDetails,
  PackageItemUpdateWithDetails,
  TLFDetails,
  DatasetDetails,
  PackageItemFootnote,
  PackageItemAcronym
} from '@/types'

const BASE_PATH = '/api/v1/packages'

// Bulk upload types
export interface BulkTLFItem {
  item_subtype: string // Table/Listing/Figure
  item_code: string
  title: string
  footnotes?: string[]
  population_flag?: string
  acronyms?: string[]
  ich_category?: string
}

export interface BulkDatasetItem {
  item_subtype: string // SDTM/ADaM
  item_code: string
  label?: string
  sorting_order?: number
}

export interface BulkUploadResponse {
  success: boolean
  created_count: number
  errors: string[]
  items: PackageItem[]
}

export const packagesApi = {
  getAll: async (): Promise<Package[]> => {
    const response = await apiClient.get(BASE_PATH)
    return response.data
  },

  getById: async (id: number): Promise<Package> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  create: async (data: PackageFormData): Promise<Package> => {
    const response = await apiClient.post(BASE_PATH, data)
    return response.data
  },

  update: async (id: number, data: PackageFormData): Promise<Package> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },

  // Package Items
  getItems: async (packageId: number): Promise<PackageItem[]> => {
    const response = await apiClient.get(`${BASE_PATH}/${packageId}/items`)
    return response.data
  },

  getItem: async (itemId: number): Promise<PackageItem> => {
    const response = await apiClient.get(`${BASE_PATH}/items/${itemId}`)
    return response.data
  },

  createItem: async (packageId: number, data: Partial<PackageItem>): Promise<PackageItem> => {
    const response = await apiClient.post(`${BASE_PATH}/${packageId}/items`, {
      ...data,
      package_id: packageId,
    })
    return response.data
  },

  // Create item with full TLF/Dataset details
  createItemWithDetails: async (packageId: number, data: PackageItemCreateWithDetails): Promise<PackageItem> => {
    const response = await apiClient.post(`${BASE_PATH}/${packageId}/items`, {
      ...data,
      package_id: packageId,
    })
    return response.data
  },

  updateItem: async (itemId: number, data: Partial<PackageItem>): Promise<PackageItem> => {
    const response = await apiClient.put(`${BASE_PATH}/items/${itemId}`, data)
    return response.data
  },

  // Update item with full TLF/Dataset details
  updateItemWithDetails: async (itemId: number, data: PackageItemUpdateWithDetails): Promise<PackageItem> => {
    const response = await apiClient.put(`${BASE_PATH}/items/${itemId}`, data)
    return response.data
  },

  deleteItem: async (itemId: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/items/${itemId}`)
  },

  // Bulk upload TLF items
  bulkCreateTLFItems: async (packageId: number, items: BulkTLFItem[]): Promise<BulkUploadResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/${packageId}/items/bulk-tlf`, items)
    return response.data
  },

  // Bulk upload Dataset items
  bulkCreateDatasetItems: async (packageId: number, items: BulkDatasetItem[]): Promise<BulkUploadResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/${packageId}/items/bulk-dataset`, items)
    return response.data
  },
}

