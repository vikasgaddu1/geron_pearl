import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, StudyRole } from '@/types'

interface AuthTokens {
  accessToken: string
  refreshToken: string
}

interface StudyRolesState {
  responsibleStudyIds: number[]
  studyRoles: Record<number, StudyRole>
}

interface AuthState {
  // User state
  currentUser: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
  isLoading: boolean
  
  // Study roles state
  studyRolesState: StudyRolesState | null
  studyRolesLoading: boolean
  
  // Actions
  setCurrentUser: (user: User | null) => void
  setTokens: (tokens: AuthTokens | null) => void
  setLoading: (loading: boolean) => void
  login: (user: User, tokens: AuthTokens) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
  setStudyRoles: (responsibleStudyIds: number[], studyRoles: Record<number, StudyRole>) => void
  setStudyRolesLoading: (loading: boolean) => void
  
  // Computed helpers
  isResponsibleForStudy: (studyId: number) => boolean
  hasResponsibleAccess: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentUser: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      studyRolesState: null,
      studyRolesLoading: false,
      
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
          studyRolesState: null,
          studyRolesLoading: false,
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
      
      // Set study roles
      setStudyRoles: (responsibleStudyIds, studyRoles) =>
        set({
          studyRolesState: { responsibleStudyIds, studyRoles },
          studyRolesLoading: false,
        }),
      
      // Set study roles loading state
      setStudyRolesLoading: (loading) =>
        set({ studyRolesLoading: loading }),
      
      // Check if user is responsible for a specific study
      isResponsibleForStudy: (studyId) => {
        const state = get()
        // Global admins have full access everywhere
        if (state.currentUser?.is_admin) return true
        // Check if user is a responsible user for this study
        return state.studyRolesState?.responsibleStudyIds.includes(studyId) ?? false
      },

      // Check if user has responsible access to any study (or is admin)
      hasResponsibleAccess: () => {
        const state = get()
        // Global admins have full access everywhere
        if (state.currentUser?.is_admin) return true
        // Check if user is responsible for at least one study
        return (state.studyRolesState?.responsibleStudyIds.length ?? 0) > 0
      },
    }),
    {
      name: 'pearl-auth-storage',
      partialize: (state) => ({
        currentUser: state.currentUser,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
        studyRolesState: state.studyRolesState,
      }),
    }
  )
)

