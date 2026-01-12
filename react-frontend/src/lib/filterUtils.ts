import { parseISO, isWithinInterval, isValid } from 'date-fns'

/**
 * Convert wildcard pattern to regex pattern
 * * matches any sequence of characters
 */
export function wildcardToRegex(pattern: string): RegExp {
  // Escape special regex characters except *
  const escaped = pattern.replace(/[.+?^${}()|[\]\\]/g, '\\$&')
  // Replace * with .*
  const regexPattern = escaped.replace(/\*/g, '.*')
  return new RegExp(`^${regexPattern}$`, 'i')
}

/**
 * Match text against wildcard pattern
 * Supports * as wildcard character
 */
export function matchWildcard(text: string, pattern: string): boolean {
  if (!pattern) return true
  if (!text) return false
  
  try {
    const regex = wildcardToRegex(pattern)
    return regex.test(text)
  } catch {
    // If regex fails, fallback to simple includes
    return text.toLowerCase().includes(pattern.toLowerCase())
  }
}

/**
 * Match text against regex pattern with error handling
 */
export function matchRegex(text: string, pattern: string): boolean {
  if (!pattern) return true
  if (!text) return false
  
  try {
    const regex = new RegExp(pattern, 'i')
    return regex.test(text)
  } catch (error) {
    // Invalid regex, return false
    console.warn('Invalid regex pattern:', pattern, error)
    return false
  }
}

/**
 * Match text with mode selection (plain, wildcard, or regex)
 */
export function matchText(
  text: string,
  pattern: string,
  mode: 'plain' | 'wildcard' | 'regex' = 'plain'
): boolean {
  if (!pattern) return true
  if (!text) return false
  
  switch (mode) {
    case 'wildcard':
      return matchWildcard(text, pattern)
    case 'regex':
      return matchRegex(text, pattern)
    case 'plain':
    default:
      return text.toLowerCase().includes(pattern.toLowerCase())
  }
}

/**
 * Check if a date falls within a date range
 */
export function matchDateRange(
  dateString: string | undefined,
  fromDate: Date | undefined,
  toDate: Date | undefined
): boolean {
  if (!fromDate && !toDate) return true
  if (!dateString) return false
  
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString
    
    if (!isValid(date)) return false
    
    // If only fromDate is set, check if date is >= fromDate
    if (fromDate && !toDate) {
      return date >= fromDate
    }
    
    // If only toDate is set, check if date is <= toDate
    if (!fromDate && toDate) {
      return date <= toDate
    }
    
    // Both dates are set, check if date is within interval
    if (fromDate && toDate) {
      return isWithinInterval(date, { start: fromDate, end: toDate })
    }
    
    return true
  } catch {
    return false
  }
}

/**
 * Match value against array of selected values
 * Used for multi-select filters
 */
export function matchMultiSelect(
  value: string | undefined,
  selectedValues: string[]
): boolean {
  if (!selectedValues || selectedValues.length === 0) return true
  if (!value) return false
  
  return selectedValues.includes(value)
}

/**
 * Detect if pattern contains wildcard characters
 */
export function hasWildcard(pattern: string): boolean {
  return pattern.includes('*')
}

/**
 * Detect if pattern looks like a regex (contains special regex chars)
 */
export function looksLikeRegex(pattern: string): boolean {
  const regexChars = /[.+?^${}()|[\]\\]/
  return regexChars.test(pattern)
}

/**
 * Extract unique values from array of objects for a given key
 */
export function getUniqueValues<T>(data: T[], key: keyof T): string[] {
  const values = data
    .map((item) => item[key])
    .filter((value) => value !== null && value !== undefined)
    .map((value) => String(value))
  
  return Array.from(new Set(values)).sort()
}











