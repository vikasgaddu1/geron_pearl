import { useEffect, useCallback } from 'react'
import { wsManager } from '@/lib/websocket'
import { useWebSocketStore } from '@/stores/websocketStore'
import type { WebSocketMessage } from '@/types'

export function useWebSocket() {
  const { status, setStatus } = useWebSocketStore()

  useEffect(() => {
    // Connect on mount
    wsManager.connect()

    // Listen for connection status changes
    const unsubscribe = wsManager.on('connection', (message) => {
      if (message.type === ('connected' as never)) {
        setStatus('connected')
      } else if (message.type === ('disconnected' as never)) {
        setStatus('disconnected')
      }
    })

    // Check initial status
    setStatus(wsManager.getStatus())

    return () => {
      unsubscribe()
    }
  }, [setStatus])

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

