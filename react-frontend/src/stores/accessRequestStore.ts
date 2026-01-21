import { create } from 'zustand'
import type { AccessRequest } from '@/types'
import { accessRequestsApi } from '@/api/endpoints/access-requests'

interface AccessRequestState {
  // State
  pendingCount: number
  pendingRequests: AccessRequest[]
  myRequests: AccessRequest[]
  isLoading: boolean
  isDropdownOpen: boolean

  // Actions
  setPendingCount: (count: number) => void
  setPendingRequests: (requests: AccessRequest[]) => void
  setMyRequests: (requests: AccessRequest[]) => void
  setLoading: (loading: boolean) => void
  setDropdownOpen: (open: boolean) => void

  // API actions
  fetchPendingCount: () => Promise<void>
  fetchPendingRequests: () => Promise<void>
  fetchMyRequests: () => Promise<void>
  approveRequest: (requestId: number) => Promise<void>
  denyRequest: (requestId: number, reason?: string) => Promise<void>

  // WebSocket handlers
  addRequest: (request: AccessRequest) => void
  updateRequest: (request: AccessRequest) => void
  removeRequest: (requestId: number) => void
}

export const useAccessRequestStore = create<AccessRequestState>((set, get) => ({
  // Initial state
  pendingCount: 0,
  pendingRequests: [],
  myRequests: [],
  isLoading: false,
  isDropdownOpen: false,

  // Setters
  setPendingCount: (count) => set({ pendingCount: count }),
  setPendingRequests: (requests) => set({ pendingRequests: requests }),
  setMyRequests: (requests) => set({ myRequests: requests }),
  setLoading: (loading) => set({ isLoading: loading }),
  setDropdownOpen: (open) => set({ isDropdownOpen: open }),

  // API actions
  fetchPendingCount: async () => {
    try {
      const data = await accessRequestsApi.getPendingCount()
      set({ pendingCount: data.pending_count })
    } catch (error) {
      console.error('Failed to fetch pending request count:', error)
    }
  },

  fetchPendingRequests: async () => {
    set({ isLoading: true })
    try {
      const data = await accessRequestsApi.list('approver', 'PENDING')
      set({ pendingRequests: data.requests, pendingCount: data.total_count, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch pending requests:', error)
      set({ isLoading: false })
    }
  },

  fetchMyRequests: async () => {
    set({ isLoading: true })
    try {
      const data = await accessRequestsApi.list('requester')
      set({ myRequests: data.requests, isLoading: false })
    } catch (error) {
      console.error('Failed to fetch my requests:', error)
      set({ isLoading: false })
    }
  },

  approveRequest: async (requestId) => {
    try {
      await accessRequestsApi.approve(requestId)
      // Remove from pending list
      const { pendingRequests, pendingCount } = get()
      set({
        pendingRequests: pendingRequests.filter((r) => r.id !== requestId),
        pendingCount: Math.max(0, pendingCount - 1),
      })
    } catch (error) {
      console.error('Failed to approve request:', error)
      throw error
    }
  },

  denyRequest: async (requestId, reason) => {
    try {
      await accessRequestsApi.deny(requestId, reason ? { denial_reason: reason } : undefined)
      // Remove from pending list
      const { pendingRequests, pendingCount } = get()
      set({
        pendingRequests: pendingRequests.filter((r) => r.id !== requestId),
        pendingCount: Math.max(0, pendingCount - 1),
      })
    } catch (error) {
      console.error('Failed to deny request:', error)
      throw error
    }
  },

  // WebSocket handlers
  addRequest: (request) => {
    const { pendingRequests, pendingCount } = get()
    // Only add to pending if status is PENDING
    if (request.status === 'PENDING') {
      set({
        pendingRequests: [request, ...pendingRequests],
        pendingCount: pendingCount + 1,
      })
    }
  },

  updateRequest: (request) => {
    const { pendingRequests, pendingCount, myRequests } = get()

    // Update in pending list or remove if resolved
    if (request.status === 'PENDING') {
      set({
        pendingRequests: pendingRequests.map((r) => (r.id === request.id ? request : r)),
      })
    } else {
      // Remove from pending if resolved
      const wasInPending = pendingRequests.some((r) => r.id === request.id)
      set({
        pendingRequests: pendingRequests.filter((r) => r.id !== request.id),
        pendingCount: wasInPending ? Math.max(0, pendingCount - 1) : pendingCount,
      })
    }

    // Update in my requests if present
    set({
      myRequests: myRequests.map((r) => (r.id === request.id ? request : r)),
    })
  },

  removeRequest: (requestId) => {
    const { pendingRequests, pendingCount, myRequests } = get()
    const wasInPending = pendingRequests.some((r) => r.id === requestId)
    set({
      pendingRequests: pendingRequests.filter((r) => r.id !== requestId),
      pendingCount: wasInPending ? Math.max(0, pendingCount - 1) : pendingCount,
      myRequests: myRequests.filter((r) => r.id !== requestId),
    })
  },
}))
