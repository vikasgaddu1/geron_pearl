/**
 * Error Reporter Utility
 * Captures frontend errors and reports them to the backend for admin viewing.
 */

import { errorLogsApi, type FrontendErrorReport } from '@/api/endpoints/error-logs'

/**
 * Generate a UUID v4 for correlation
 */
function generateCorrelationId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

/**
 * Get browser and OS information
 */
function getBrowserInfo(): string {
  try {
    const { userAgent, language, platform } = navigator
    return JSON.stringify({
      userAgent: userAgent.substring(0, 200),
      language,
      platform,
      viewport: `${window.innerWidth}x${window.innerHeight}`,
      url: window.location.href.substring(0, 200),
    })
  } catch {
    return '{}'
  }
}

interface ErrorContext {
  componentName?: string
  additionalInfo?: Record<string, unknown>
}

/**
 * Report a general error to the backend
 * @param error - Error object or string message
 * @param severity - Severity level (default: ERROR)
 * @param context - Additional context like component name
 */
export function reportError(
  error: Error | string,
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL' = 'ERROR',
  context?: ErrorContext
): void {
  const errorObj = error instanceof Error ? error : new Error(String(error))

  const report: FrontendErrorReport = {
    severity,
    error_type: errorObj.name || 'Error',
    message: errorObj.message.substring(0, 2000),
    stack_trace: errorObj.stack?.substring(0, 10000),
    component_name: context?.componentName,
    request_path: window.location.pathname,
    browser_info: getBrowserInfo(),
    correlation_id: generateCorrelationId(),
  }

  // Fire and forget - don't await or catch
  errorLogsApi.report(report)
}

/**
 * Report an API error to the backend
 * @param error - The error from an API call
 * @param endpoint - The API endpoint that failed
 * @param method - The HTTP method used
 */
export function reportApiError(
  error: unknown,
  endpoint: string,
  method: string
): void {
  const message = error instanceof Error ? error.message : String(error)
  const stack = error instanceof Error ? error.stack : undefined

  const report: FrontendErrorReport = {
    severity: 'ERROR',
    error_type: 'APIError',
    message: `${method.toUpperCase()} ${endpoint}: ${message}`.substring(0, 2000),
    stack_trace: stack?.substring(0, 10000),
    request_path: endpoint,
    browser_info: getBrowserInfo(),
    correlation_id: generateCorrelationId(),
  }

  // Fire and forget
  errorLogsApi.report(report)
}

/**
 * Report a React Error Boundary error
 * @param error - The caught error
 * @param errorInfo - React error info containing component stack
 */
export function reportBoundaryError(
  error: Error,
  errorInfo?: { componentStack?: string }
): void {
  // Try to extract component name from stack
  const componentName = errorInfo?.componentStack
    ?.split('\n')
    .find(line => line.trim().startsWith('at '))
    ?.trim()
    .replace(/^at /, '')
    .split(' ')[0] || 'Unknown'

  const report: FrontendErrorReport = {
    severity: 'CRITICAL',
    error_type: error.name || 'ReactError',
    message: error.message.substring(0, 2000),
    stack_trace: (error.stack || '') + '\n\nComponent Stack:\n' + (errorInfo?.componentStack || ''),
    component_name: componentName,
    request_path: window.location.pathname,
    browser_info: getBrowserInfo(),
    correlation_id: generateCorrelationId(),
  }

  // Fire and forget
  errorLogsApi.report(report)
}
