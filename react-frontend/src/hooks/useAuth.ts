import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuthStore } from '@/stores/authStore'
import { authApi, type LoginRequest } from '@/api/endpoints/auth'

export function useAuth() {
  const navigate = useNavigate()
  const { currentUser, isAuthenticated, isLoading, login, logout: storeLogout, setLoading } = useAuthStore()

  const loginUser = async (credentials: LoginRequest) => {
    try {
      setLoading(true)
      const response = await authApi.login(credentials)
      
      login(response.user, {
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
      })
      
      toast.success('Login successful!')
      navigate('/dashboard')
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed. Please check your credentials.'
      toast.error(message)
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
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to send reset email'
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
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to reset password'
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
  }
}

