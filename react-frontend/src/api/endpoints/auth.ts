import { apiClient } from '../client'
import type { User } from '@/types'

const BASE_PATH = '/api/v1/auth'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirm_password: string
  role?: string
  department?: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ForgotPasswordResponse {
  message: string
}

export interface ResetPasswordRequest {
  token: string
  new_password: string
  confirm_password: string
}

export interface ResetPasswordResponse {
  message: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
  confirm_password: string
}

export interface ChangePasswordResponse {
  message: string
}

export const authApi = {
  /**
   * Login with username and password
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/login`, credentials)
    return response.data
  },

  /**
   * Register a new user
   */
  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await apiClient.post(`${BASE_PATH}/register`, userData)
    return response.data
  },

  /**
   * Refresh access token using refresh token
   */
  refreshToken: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/refresh`, {
      refresh_token: refreshToken,
    })
    return response.data
  },

  /**
   * Logout (client-side token removal primarily)
   */
  logout: async (): Promise<void> => {
    await apiClient.post(`${BASE_PATH}/logout`)
  },

  /**
   * Get current user information
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get(`${BASE_PATH}/me`)
    return response.data
  },

  /**
   * Request password reset
   */
  forgotPassword: async (email: string): Promise<ForgotPasswordResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/forgot-password`, {
      email,
    })
    return response.data
  },

  /**
   * Reset password with token
   */
  resetPassword: async (data: ResetPasswordRequest): Promise<ResetPasswordResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/reset-password`, data)
    return response.data
  },

  /**
   * Change password (authenticated)
   */
  changePassword: async (data: ChangePasswordRequest): Promise<ChangePasswordResponse> => {
    const response = await apiClient.post(`${BASE_PATH}/change-password`, data)
    return response.data
  },

  /**
   * Initiate OAuth2 login
   */
  loginWithOAuth: (provider: 'google' | 'microsoft' | 'github'): void => {
    window.location.href = `${import.meta.env.VITE_API_BASE_URL || ''}${BASE_PATH}/login/${provider}`
  },
}

