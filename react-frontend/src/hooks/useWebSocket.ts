import { useEffect, useCallback } from 'react'
import { wsManager } from '@/lib/websocket'
import { useWebSocketStore } from '@/stores/websocketStore'
import { useNotificationStore } from '@/stores/notificationStore'
import { useAuthStore } from '@/stores/authStore'
import type { WebSocketMessage } from '@/types'

export function useWebSocket() {
  const { status, setStatus } = useWebSocketStore()
  const { addNotification, updateCount, fetchCount } = useNotificationStore()
  const { currentUser } = useAuthStore()

  useEffect(() => {
    // Connect on mount
    wsManager.connect()

    // Listen for connection status changes
    const unsubscribeConnection = wsManager.on('connection', (message) => {
      if (message.type === ('connected' as never)) {
        setStatus('connected')
        // Refresh notification count on reconnect
        if (currentUser) {
          fetchCount()
        }
      } else if (message.type === ('disconnected' as never)) {
        setStatus('disconnected')
      }
    })

    // Listen for notification events
    const unsubscribeNotificationCreated = wsManager.on('notification_created', (message) => {
      const data = message.data as { user_id: number; notification: never }
      // Only add if notification is for current user
      if (currentUser && data.user_id === currentUser.id) {
        addNotification(data.notification)
      }
    })

    const unsubscribeNotificationCount = wsManager.on('notification_count_updated', (message) => {
      const data = message.data as { user_id: number; unread_count: number }
      // Only update if count is for current user
      if (currentUser && data.user_id === currentUser.id) {
        updateCount(data.unread_count)
      }
    })

    // Check initial status
    setStatus(wsManager.getStatus())

    return () => {
      unsubscribeConnection()
      unsubscribeNotificationCreated()
      unsubscribeNotificationCount()
    }
  }, [setStatus, addNotification, updateCount, fetchCount, currentUser])

  return { status, isConnected: status === 'connected' }
}

export function useWebSocketEvent(
  eventType: string | string[],
  handler: (message: WebSocketMessage) => void
) {
  useEffect(() => {
    const events = Array.isArray(eventType) ? eventType : [eventType]
    const unsubscribes: (() => void)[] = []

    events.forEach((event) => {
      const unsubscribe = wsManager.on(event, handler)
      unsubscribes.push(unsubscribe)
    })

    return () => {
      unsubscribes.forEach((unsubscribe) => unsubscribe())
    }
  }, [eventType, handler])
}

export function useWebSocketRefresh(
  entityTypes: string[],
  onRefresh: () => void
) {
  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      // Check if the message type starts with any of the entity types
      const shouldRefresh = entityTypes.some((type) =>
        message.type.startsWith(type)
      )
      if (shouldRefresh) {
        onRefresh()
      }
    },
    [entityTypes, onRefresh]
  )

  useWebSocketEvent('*', handleMessage)
}










