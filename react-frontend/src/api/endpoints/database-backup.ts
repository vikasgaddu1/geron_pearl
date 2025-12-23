import { apiClient } from '../client'
import type { DatabaseBackup } from '@/types'

const BASE_PATH = '/api/v1/database-backup'

export interface BackupStatus {
  backup_directory: string
  total_backups: number
  latest_backup?: DatabaseBackup
}

export const databaseBackupApi = {
  create: async (description?: string): Promise<DatabaseBackup> => {
    const response = await apiClient.post(
      `${BASE_PATH}/create`,
      description ? { description } : null,
      { headers: { 'X-User-Role': 'admin' } }
    )
    return response.data
  },

  list: async (): Promise<DatabaseBackup[]> => {
    const response = await apiClient.get(`${BASE_PATH}/list`, {
      headers: { 'X-User-Role': 'admin' },
    })
    return response.data
  },

  delete: async (filename: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/delete/${filename}`, {
      headers: { 'X-User-Role': 'admin' },
    })
  },

  restore: async (filename: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/restore/${filename}`, null, {
      headers: { 'X-User-Role': 'admin' },
    })
    return response.data
  },

  getStatus: async (): Promise<BackupStatus> => {
    const response = await apiClient.get(`${BASE_PATH}/status`, {
      headers: { 'X-User-Role': 'admin' },
    })
    return response.data
  },
}

