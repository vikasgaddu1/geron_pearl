import { apiClient } from '../client'

const BASE_PATH = '/api/v1/notifications'

export interface NotificationData {
  id: number
  user_id: number
  tracker_id?: number
  triggered_by_user_id?: number
  notification_type: 'assignment_prod' | 'assignment_qc' | 'comment_added'
  title: string
  message: string
  item_code?: string
  study_label?: string
  is_read: boolean
  is_acknowledged: boolean
  created_at: string
  read_at?: string
  acknowledged_at?: string
  triggered_by_username?: string
}

export interface NotificationCountResponse {
  unread_count: number
  total_unacknowledged: number
}

export const notificationsApi = {
  /**
   * Get notifications for the current user
   */
  getNotifications: async (limit = 50): Promise<NotificationData[]> => {
    const response = await apiClient.get(`${BASE_PATH}/`, { params: { limit } })
    return response.data
  },

  /**
   * Get notification counts
   */
  getCount: async (): Promise<NotificationCountResponse> => {
    const response = await apiClient.get(`${BASE_PATH}/count`)
    return response.data
  },

  /**
   * Mark a notification as read
   */
  markAsRead: async (notificationId: number): Promise<NotificationData> => {
    const response = await apiClient.post(`${BASE_PATH}/${notificationId}/read`)
    return response.data
  },

  /**
   * Acknowledge (dismiss) a notification
   */
  acknowledge: async (notificationId: number): Promise<NotificationData> => {
    const response = await apiClient.post(`${BASE_PATH}/${notificationId}/acknowledge`)
    return response.data
  },

  /**
   * Mark all notifications as read
   */
  markAllAsRead: async (): Promise<{ message: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/read-all`)
    return response.data
  },

  /**
   * Acknowledge all notifications
   */
  acknowledgeAll: async (): Promise<{ message: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/acknowledge-all`)
    return response.data
  },
}
