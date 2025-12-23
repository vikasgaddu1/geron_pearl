import { Badge } from "@/components/ui/badge"
import type { TrackerStatus, Priority } from "@/types"

interface StatusBadgeProps {
  status: TrackerStatus
}

const statusConfig: Record<TrackerStatus, { label: string; variant: "default" | "secondary" | "success" | "warning" | "destructive" | "info" }> = {
  not_started: { label: "Not Started", variant: "secondary" },
  in_progress: { label: "In Progress", variant: "info" },
  completed: { label: "Completed", variant: "success" },
  on_hold: { label: "On Hold", variant: "warning" },
  failed: { label: "Failed", variant: "destructive" },
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] || { label: status, variant: "secondary" as const }
  return <Badge variant={config.variant}>{config.label}</Badge>
}

interface PriorityBadgeProps {
  priority: Priority
}

const priorityConfig: Record<Priority, { label: string; className: string }> = {
  critical: { label: "Critical", className: "bg-red-600 text-white" },
  high: { label: "High", className: "bg-orange-500 text-white" },
  medium: { label: "Medium", className: "bg-yellow-500 text-white" },
  low: { label: "Low", className: "bg-gray-500 text-white" },
}

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  const config = priorityConfig[priority] || { label: priority, className: "bg-gray-500 text-white" }
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  )
}

interface RoleBadgeProps {
  role: string
}

const roleConfig: Record<string, { className: string }> = {
  admin: { className: "bg-purple-600 text-white" },
  lead: { className: "bg-blue-600 text-white" },
  programmer: { className: "bg-green-600 text-white" },
  analyst: { className: "bg-cyan-600 text-white" },
  viewer: { className: "bg-gray-500 text-white" },
}

export function RoleBadge({ role }: RoleBadgeProps) {
  const config = roleConfig[role.toLowerCase()] || { className: "bg-gray-500 text-white" }
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ${config.className}`}>
      {role}
    </span>
  )
}

