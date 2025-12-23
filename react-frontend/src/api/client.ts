import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth headers if needed
apiClient.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
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

