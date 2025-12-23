import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/authStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: Error | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve()
    }
  })
  failedQueue = []
}

// Request interceptor for adding auth headers
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { tokens } = useAuthStore.getState()
    
    // Skip auth header for auth endpoints
    const isAuthEndpoint = config.url?.includes('/auth/')
    
    if (tokens?.accessToken && !isAuthEndpoint) {
      config.headers.Authorization = `Bearer ${tokens.accessToken}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    
    // Handle 401 Unauthorized errors (expired/invalid token)
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Skip refresh for auth endpoints
      if (originalRequest.url?.includes('/auth/')) {
        return Promise.reject(error)
      }
      
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(() => {
            return apiClient(originalRequest)
          })
          .catch((err) => {
            return Promise.reject(err)
          })
      }
      
      originalRequest._retry = true
      isRefreshing = true
      
      const { tokens, logout } = useAuthStore.getState()
      
      if (!tokens?.refreshToken) {
        // No refresh token available, logout
        logout()
        isRefreshing = false
        processQueue(new Error('No refresh token available'))
        window.location.href = '/login'
        return Promise.reject(error)
      }
      
      try {
        // Attempt to refresh the token
        const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: tokens.refreshToken,
        })
        
        const { access_token, refresh_token } = response.data
        
        // Update tokens in store
        useAuthStore.getState().setTokens({
          accessToken: access_token,
          refreshToken: refresh_token,
        })
        
        // Update the authorization header
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        
        // Process queued requests
        processQueue()
        isRefreshing = false
        
        // Retry the original request
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed, logout user
        processQueue(refreshError as Error)
        isRefreshing = false
        logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    
    // Handle other errors
    if (error.response) {
      // Server responded with error
      const message = error.response.data?.detail || error.response.data?.message || 'An error occurred'
      console.error('API Error:', message)
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error: No response received')
    } else {
      // Request setup error
      console.error('Request Error:', error.message)
    }
    
    return Promise.reject(error)
  }
)

// Health check
export async function checkHealth(): Promise<{ status: string }> {
  const response = await apiClient.get('/health')
  return response.data
}

