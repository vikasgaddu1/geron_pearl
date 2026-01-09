import { create } from 'zustand'
import type { NotificationData } from '@/api/endpoints/notifications'
import { notificationsApi } from '@/api/endpoints/notifications'

interface NotificationState {
  // State
  notifications: NotificationData[]
  unreadCount: number
  isLoading: boolean
  isDropdownOpen: boolean
  
  // Actions
  setNotifications: (notifications: NotificationData[]) => void
  setUnreadCount: (count: number) => void
  setLoading: (loading: boolean) => void
  setDropdownOpen: (open: boolean) => void
  
  // API actions
  fetchNotifications: () => Promise<void>
  fetchCount: () => Promise<void>
  markAsRead: (notificationId: number) => Promise<void>
  acknowledge: (notificationId: number) => Promise<void>
  acknowledgeAll: () => Promise<void>
  
  // WebSocket handlers
  addNotification: (notification: NotificationData) => void
  updateCount: (count: number) => void
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  // Initial state
  notifications: [],
  unreadCount: 0,
  isLoading: false,
  isDropdownOpen: false,
  
  // Setters
  setNotifications: (notifications) => set({ notifications }),
  setUnreadCount: (count) => set({ unreadCount: count }),
  setLoading: (loading) => set({ isLoading: loading }),
  setDropdownOpen: (open) => set({ isDropdownOpen: open }),
  
  // API actions
  fetchNotifications: async () => {
    set({ isLoading: true })
    try {
      const notifications = await notificationsApi.getNotifications()
      set({ notifications, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
      set({ isLoading: false })
    }
  },
  
  fetchCount: async () => {
    try {
      const data = await notificationsApi.getCount()
      set({ unreadCount: data.unread_count })
    } catch (error) {
      console.error('Failed to fetch notification count:', error)
    }
  },
  
  markAsRead: async (notificationId) => {
    try {
      await notificationsApi.markAsRead(notificationId)
      // Update local state
      const { notifications, unreadCount } = get()
      set({
        notifications: notifications.map((n) =>
          n.id === notificationId ? { ...n, is_read: true } : n
        ),
        unreadCount: Math.max(0, unreadCount - 1),
      })
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
    }
  },
  
  acknowledge: async (notificationId) => {
    try {
      await notificationsApi.acknowledge(notificationId)
      // Remove from local state
      const { notifications, unreadCount } = get()
      const notif = notifications.find((n) => n.id === notificationId)
      set({
        notifications: notifications.filter((n) => n.id !== notificationId),
        unreadCount: notif && !notif.is_read ? Math.max(0, unreadCount - 1) : unreadCount,
      })
    } catch (error) {
      console.error('Failed to acknowledge notification:', error)
    }
  },
  
  acknowledgeAll: async () => {
    try {
      await notificationsApi.acknowledgeAll()
      set({ notifications: [], unreadCount: 0 })
    } catch (error) {
      console.error('Failed to acknowledge all notifications:', error)
    }
  },
  
  // WebSocket handlers
  addNotification: (notification) => {
    const { notifications, unreadCount } = get()
    // Add to beginning of list (most recent first)
    set({
      notifications: [notification, ...notifications],
      unreadCount: unreadCount + 1,
    })
  },
  
  updateCount: (count) => {
    set({ unreadCount: count })
  },
}))
