import { apiClient } from '../client'
import type { UseCase, UseCaseFormData, UseCaseSummary, BulkUseCaseAssignment, BulkOperationResult } from '@/types'

const BASE_PATH = '/api/v1/use-cases'

// ==================== Use Case CRUD ====================

export const getAllUseCases = async (): Promise<UseCase[]> => {
  const response = await apiClient.get<UseCase[]>(`${BASE_PATH}/`)
  return response.data
}

export const getUseCase = async (id: number): Promise<UseCase> => {
  const response = await apiClient.get<UseCase>(`${BASE_PATH}/${id}`)
  return response.data
}

export const createUseCase = async (data: UseCaseFormData): Promise<UseCase> => {
  const response = await apiClient.post<UseCase>(`${BASE_PATH}/`, data)
  return response.data
}

export const updateUseCase = async (id: number, data: Partial<UseCaseFormData>): Promise<UseCase> => {
  const response = await apiClient.put<UseCase>(`${BASE_PATH}/${id}`, data)
  return response.data
}

export const deleteUseCase = async (id: number): Promise<void> => {
  await apiClient.delete(`${BASE_PATH}/${id}`)
}

// ==================== Assignments ====================

export const assignUseCase = async (reportingEffortId: number, useCaseId: number): Promise<void> => {
  await apiClient.post(`${BASE_PATH}/assign`, {
    reporting_effort_id: reportingEffortId,
    use_case_id: useCaseId
  })
}

export const removeUseCaseAssignment = async (reportingEffortId: number, useCaseId: number): Promise<void> => {
  await apiClient.delete(`${BASE_PATH}/assign/${reportingEffortId}/${useCaseId}`)
}

export const getUseCasesForEffort = async (reportingEffortId: number): Promise<UseCaseSummary[]> => {
  const response = await apiClient.get<UseCaseSummary[]>(`${BASE_PATH}/effort/${reportingEffortId}`)
  return response.data
}

export const getEffortsByUseCase = async (useCaseId: number): Promise<number[]> => {
  const response = await apiClient.get<number[]>(`${BASE_PATH}/by-use-case/${useCaseId}/efforts`)
  return response.data
}

// ==================== Bulk Operations ====================

export const bulkAssignUseCase = async (data: BulkUseCaseAssignment): Promise<BulkOperationResult> => {
  const response = await apiClient.post<BulkOperationResult>(`${BASE_PATH}/bulk-assign`, data)
  return response.data
}

export const bulkRemoveUseCase = async (data: BulkUseCaseAssignment): Promise<BulkOperationResult> => {
  const response = await apiClient.post<BulkOperationResult>(`${BASE_PATH}/bulk-remove`, data)
  return response.data
}

export const bulkGetUseCases = async (reportingEffortIds: number[]): Promise<Record<number, UseCaseSummary[]>> => {
  const response = await apiClient.post<Record<number, UseCaseSummary[]>>(`${BASE_PATH}/bulk-get`, reportingEffortIds)
  return response.data
}
