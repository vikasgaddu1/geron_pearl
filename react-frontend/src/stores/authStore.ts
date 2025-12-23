import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'

interface AuthState {
  currentUser: User | null
  selectedUserId: number | null
  setCurrentUser: (user: User | null) => void
  setSelectedUserId: (id: number | null) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      currentUser: null,
      selectedUserId: null,
      setCurrentUser: (user) => set({ currentUser: user }),
      setSelectedUserId: (id) => set({ selectedUserId: id }),
    }),
    {
      name: 'pearl-auth-storage',
    }
  )
)

