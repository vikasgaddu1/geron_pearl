import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { AxiosError } from 'axios'
import { useAuthStore } from '@/stores/authStore'
import { authApi, type LoginRequest } from '@/api/endpoints/auth'

interface ApiErrorResponse {
  detail?: string
}

export function useAuth() {
  const navigate = useNavigate()
  const {
    currentUser,
    isAuthenticated,
    isLoading,
    login,
    logout: storeLogout,
    setLoading,
    setStudyRoles,
    setStudyRolesLoading,
    hasResponsibleAccess,
    isResponsibleForStudy,
    studyRolesState,
    studyRolesLoading,
  } = useAuthStore()

  // Fetch and set study roles
  const fetchStudyRoles = async () => {
    try {
      setStudyRolesLoading(true)
      const studyRolesData = await authApi.getMyStudyRoles()
      setStudyRoles(studyRolesData.responsible_study_ids, studyRolesData.study_roles)
    } catch (error) {
      console.error('Failed to fetch study roles:', error)
      setStudyRolesLoading(false)
    }
  }

  const loginUser = async (credentials: LoginRequest) => {
    try {
      setLoading(true)
      // Clear stale study roles immediately to prevent showing unauthorized items
      setStudyRoles([], {})
      setStudyRolesLoading(true)
      
      const response = await authApi.login(credentials)
      
      login(response.user, {
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
      })
      
      // Fetch study roles after successful login
      try {
        const studyRolesData = await authApi.getMyStudyRoles()
        setStudyRoles(studyRolesData.responsible_study_ids, studyRolesData.study_roles)
      } catch (roleError) {
        console.error('Failed to fetch study roles:', roleError)
        setStudyRolesLoading(false)
      }
      
      toast.success('Login successful!')
      navigate('/dashboard')
    } catch (error) {
      const axiosError = error as AxiosError<ApiErrorResponse>
      const message = axiosError.response?.data?.detail || 'Login failed. Please check your credentials.'
      toast.error(message)
      setStudyRolesLoading(false)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logoutUser = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout API call failed:', error)
    } finally {
      storeLogout()
      toast.success('Logged out successfully')
      navigate('/login')
    }
  }

  const forgotPassword = async (email: string) => {
    try {
      const response = await authApi.forgotPassword(email)
      toast.success(response.message)
      return response
    } catch (error) {
      const axiosError = error as AxiosError<ApiErrorResponse>
      const message = axiosError.response?.data?.detail || 'Failed to send reset email'
      toast.error(message)
      throw error
    }
  }

  const resetPassword = async (token: string, newPassword: string, confirmPassword: string) => {
    try {
      const response = await authApi.resetPassword({
        token,
        new_password: newPassword,
        confirm_password: confirmPassword,
      })
      toast.success(response.message)
      navigate('/login')
      return response
    } catch (error) {
      const axiosError = error as AxiosError<ApiErrorResponse>
      const message = axiosError.response?.data?.detail || 'Failed to reset password'
      toast.error(message)
      throw error
    }
  }

  return {
    currentUser,
    isAuthenticated,
    isLoading,
    login: loginUser,
    logout: logoutUser,
    forgotPassword,
    resetPassword,
    fetchStudyRoles,
    hasResponsibleAccess,
    isResponsibleForStudy,
    studyRolesState,
    studyRolesLoading,
  }
}










