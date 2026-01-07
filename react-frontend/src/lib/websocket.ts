import type { WebSocketMessage, WebSocketEventType } from '@/types'

type MessageHandler = (message: WebSocketMessage) => void

interface WebSocketManagerOptions {
  url: string
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

class WebSocketManager {
  private ws: WebSocket | null = null
  private url: string
  private reconnectInterval: number
  private maxReconnectAttempts: number
  private reconnectAttempts = 0
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private isConnecting = false
  private shouldReconnect = true

  constructor(options: WebSocketManagerOptions) {
    this.url = options.url
    this.reconnectInterval = options.reconnectInterval || 3000
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return
    }

    this.isConnecting = true
    this.shouldReconnect = true

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.emit('connection', { type: 'connected' as WebSocketEventType, data: {}, timestamp: new Date().toISOString() })
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          this.emit(message.type, message)
          this.emit('*', message) // Wildcard for all messages
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.isConnecting = false
        this.emit('connection', { type: 'disconnected' as WebSocketEventType, data: {}, timestamp: new Date().toISOString() })
        this.attemptReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.isConnecting = false
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      this.isConnecting = false
      this.attemptReconnect()
    }
  }

  private attemptReconnect(): void {
    if (!this.shouldReconnect || this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached or reconnection disabled')
      return
    }

    this.reconnectAttempts++
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)

    setTimeout(() => {
      this.connect()
    }, this.reconnectInterval)
  }

  disconnect(): void {
    this.shouldReconnect = false
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  on(event: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set())
    }
    this.handlers.get(event)!.add(handler)

    // Return unsubscribe function
    return () => {
      this.handlers.get(event)?.delete(handler)
    }
  }

  off(event: string, handler: MessageHandler): void {
    this.handlers.get(event)?.delete(handler)
  }

  private emit(event: string, message: WebSocketMessage): void {
    this.handlers.get(event)?.forEach((handler) => handler(message))
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  getStatus(): 'connected' | 'connecting' | 'disconnected' {
    if (this.ws?.readyState === WebSocket.OPEN) return 'connected'
    if (this.isConnecting) return 'connecting'
    return 'disconnected'
  }
}

// Singleton instance
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws/studies'
export const wsManager = new WebSocketManager({ url: WS_URL })

export default WebSocketManager









