import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'

interface AuthTokens {
  accessToken: string
  refreshToken: string
}

interface AuthState {
  // User state
  currentUser: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
  isLoading: boolean
  
  // Actions
  setCurrentUser: (user: User | null) => void
  setTokens: (tokens: AuthTokens | null) => void
  setLoading: (loading: boolean) => void
  login: (user: User, tokens: AuthTokens) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentUser: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      
      // Set current user
      setCurrentUser: (user) =>
        set({
          currentUser: user,
          isAuthenticated: !!user,
        }),
      
      // Set authentication tokens
      setTokens: (tokens) =>
        set({ tokens }),
      
      // Set loading state
      setLoading: (loading) =>
        set({ isLoading: loading }),
      
      // Login action - sets user and tokens
      login: (user, tokens) =>
        set({
          currentUser: user,
          tokens,
          isAuthenticated: true,
          isLoading: false,
        }),
      
      // Logout action - clears everything
      logout: () =>
        set({
          currentUser: null,
          tokens: null,
          isAuthenticated: false,
          isLoading: false,
        }),
      
      // Update user information
      updateUser: (userData) => {
        const current = get().currentUser
        if (current) {
          set({
            currentUser: { ...current, ...userData },
          })
        }
      },
    }),
    {
      name: 'pearl-auth-storage',
      partialize: (state) => ({
        currentUser: state.currentUser,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

