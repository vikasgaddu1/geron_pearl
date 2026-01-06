import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { AxiosError } from "axios"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Extract a user-friendly error message from various error types
 * Handles Axios errors, FastAPI validation errors, and generic errors
 */
export function getErrorMessage(error: unknown, fallback = 'An unexpected error occurred'): string {
  // Handle Axios errors
  if (error instanceof AxiosError || (error && typeof error === 'object' && 'isAxiosError' in error)) {
    const axiosError = error as AxiosError<{
      detail?: string | { msg: string; loc?: string[] }[] | { message: string }
      message?: string
      error?: string
    }>
    
    const data = axiosError.response?.data
    
    if (data) {
      // FastAPI HTTPException detail (string)
      if (typeof data.detail === 'string') {
        return data.detail
      }
      
      // FastAPI validation errors (array of {msg, loc})
      if (Array.isArray(data.detail)) {
        const messages = data.detail.map((err) => {
          if (typeof err === 'string') return err
          const location = err.loc?.join(' → ') || ''
          return location ? `${location}: ${err.msg}` : err.msg
        })
        return messages.join('; ')
      }
      
      // Object with message property
      if (data.detail && typeof data.detail === 'object' && 'message' in data.detail) {
        return data.detail.message
      }
      
      // Generic message field
      if (data.message) {
        return data.message
      }
      
      // Generic error field
      if (data.error) {
        return data.error
      }
    }
    
    // HTTP status-based messages
    const status = axiosError.response?.status
    if (status) {
      switch (status) {
        case 400: return 'Bad request - please check your input'
        case 401: return 'Authentication required - please log in'
        case 403: return 'Access denied - you don\'t have permission'
        case 404: return 'Resource not found'
        case 409: return 'Conflict - this item may already exist'
        case 422: return 'Validation error - please check your input'
        case 500: return 'Server error - please try again later'
        case 502: return 'Server unavailable - please try again later'
        case 503: return 'Service temporarily unavailable'
      }
    }
    
    // Network error
    if (axiosError.code === 'ERR_NETWORK') {
      return 'Network error - please check your connection'
    }
    
    // Timeout
    if (axiosError.code === 'ECONNABORTED') {
      return 'Request timed out - please try again'
    }
  }
  
  // Handle standard Error objects
  if (error instanceof Error) {
    return error.message || fallback
  }
  
  // Handle string errors
  if (typeof error === 'string') {
    return error
  }
  
  return fallback
}

/**
 * Validate email format
 * Returns true if email is valid, false otherwise
 */
export function isValidEmail(email: string): boolean {
  if (!email || email.trim() === '') {
    return false;
  }
  // RFC 5322 compliant email regex (simplified version)
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
}

export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return '-'
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return '-'
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'
  return d.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date()
  const then = new Date(date)
  const diffMs = now.getTime() - then.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(date)
}

/**
 * Generate a cryptographically secure random password.
 * Uses browser crypto API for secure random generation.
 * 
 * @param length Desired password length (default: 12)
 * @returns Secure random password string with mix of character types
 */
export function generateSecurePassword(length: number = 12): string {
  const lowercase = 'abcdefghijklmnopqrstuvwxyz'
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const digits = '0123456789'
  const special = '!@#$%^&*'
  const allChars = lowercase + uppercase + digits + special
  
  // Get cryptographically secure random values
  const randomValues = new Uint32Array(length)
  crypto.getRandomValues(randomValues)
  
  // Ensure at least one character from each set
  const passwordChars = [
    lowercase[randomValues[0] % lowercase.length],
    uppercase[randomValues[1] % uppercase.length],
    digits[randomValues[2] % digits.length],
    special[randomValues[3] % special.length],
  ]
  
  // Fill the rest with random characters from all sets
  for (let i = 4; i < length; i++) {
    passwordChars.push(allChars[randomValues[i] % allChars.length])
  }
  
  // Shuffle to avoid predictable pattern
  for (let i = passwordChars.length - 1; i > 0; i--) {
    const j = randomValues[i % randomValues.length] % (i + 1)
    ;[passwordChars[i], passwordChars[j]] = [passwordChars[j], passwordChars[i]]
  }
  
  return passwordChars.join('')
}


