import { create } from 'zustand'

type ConnectionStatus = 'connected' | 'connecting' | 'disconnected'

interface WebSocketState {
  status: ConnectionStatus
  setStatus: (status: ConnectionStatus) => void
}

export const useWebSocketStore = create<WebSocketState>((set) => ({
  status: 'disconnected',
  setStatus: (status) => set({ status }),
}))

