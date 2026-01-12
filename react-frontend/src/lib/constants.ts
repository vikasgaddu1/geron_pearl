/**
 * Shared color constants used across the application
 */

// Priority badge colors (Tailwind classes for Badge components)
export const PRIORITY_BADGE_COLORS: Record<string, string> = {
  critical: 'bg-red-500 text-white',
  high: 'bg-orange-500 text-white',
  medium: 'bg-yellow-500 text-black',
  low: 'bg-green-500 text-white',
}

// Priority colors for charts (hex values)
export const PRIORITY_CHART_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
}

// Status colors for charts (hex values)
export const STATUS_CHART_COLORS: Record<string, string> = {
  not_started: '#6b7280',
  in_progress: '#3b82f6',
  ready_for_qc: '#8b5cf6',
  completed: '#22c55e',
  on_hold: '#eab308',
  failed: '#ef4444',
}

// Item type colors for charts (hex values)
export const ITEM_TYPE_CHART_COLORS: Record<string, string> = {
  table: '#3b82f6',    // Blue
  listing: '#8b5cf6',  // Purple
  figure: '#ec4899',   // Pink
  SDTM: '#14b8a6',     // Teal
  ADaM: '#f59e0b',     // Amber
  Unknown: '#6b7280',  // Gray
}

// Preset colors for tags (hex values)
export const TAG_PRESET_COLORS = [
  '#EF4444', // Red
  '#F97316', // Orange
  '#F59E0B', // Amber
  '#84CC16', // Lime
  '#22C55E', // Green
  '#14B8A6', // Teal
  '#06B6D4', // Cyan
  '#3B82F6', // Blue
  '#6366F1', // Indigo
  '#8B5CF6', // Violet
  '#A855F7', // Purple
  '#EC4899', // Pink
] as const

// Helper to format priority for display
export function formatPriority(priority: string | undefined | null): string {
  const p = priority || 'medium'
  return p.charAt(0).toUpperCase() + p.slice(1)
}
