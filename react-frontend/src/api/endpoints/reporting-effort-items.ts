import { apiClient } from '../client'
import type { ReportingEffortItem, BulkOperationResult } from '@/types'

const BASE_PATH = '/api/v1/reporting-effort-items'

export const reportingEffortItemsApi = {
  getAll: async (): Promise<ReportingEffortItem[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`)
    return response.data
  },

  getById: async (id: number): Promise<ReportingEffortItem> => {
    const response = await apiClient.get(`${BASE_PATH}/${id}`)
    return response.data
  },

  getByEffortId: async (effortId: number): Promise<ReportingEffortItem[]> => {
    const response = await apiClient.get(`${BASE_PATH}/by-effort/${effortId}`)
    return response.data
  },

  create: async (data: Partial<ReportingEffortItem>): Promise<ReportingEffortItem> => {
    const response = await apiClient.post(`${BASE_PATH}/`, data)
    return response.data
  },

  update: async (id: number, data: Partial<ReportingEffortItem>): Promise<ReportingEffortItem> => {
    const response = await apiClient.put(`${BASE_PATH}/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}`)
  },

  // Bulk operations
  bulkUploadTLF: async (effortId: number, file: File): Promise<BulkOperationResult> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post(`${BASE_PATH}/${effortId}/bulk-tlf`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  bulkUploadDataset: async (effortId: number, file: File): Promise<BulkOperationResult> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await apiClient.post(`${BASE_PATH}/${effortId}/bulk-dataset`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  copyFromPackage: async (effortId: number, packageId: number): Promise<BulkOperationResult> => {
    const response = await apiClient.post(`${BASE_PATH}/${effortId}/copy-from-package`, {
      package_id: packageId,
    })
    return response.data
  },

  copyTLFFromPackage: async (effortId: number, packageId: number): Promise<BulkOperationResult> => {
    const response = await apiClient.post(`${BASE_PATH}/${effortId}/copy-tlf-from-package`, {
      package_id: packageId,
    })
    return response.data
  },

  copyDatasetFromPackage: async (effortId: number, packageId: number): Promise<BulkOperationResult> => {
    const response = await apiClient.post(`${BASE_PATH}/${effortId}/copy-dataset-from-package`, {
      package_id: packageId,
    })
    return response.data
  },

  copyFromReportingEffort: async (effortId: number, sourceEffortId: number): Promise<BulkOperationResult> => {
    const response = await apiClient.post(`${BASE_PATH}/${effortId}/copy-from-reporting-effort`, {
      source_reporting_effort_id: sourceEffortId,
    })
    return response.data
  },
}

