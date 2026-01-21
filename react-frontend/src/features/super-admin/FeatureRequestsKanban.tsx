import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bug, Lightbulb, Clock, Loader2, CheckCircle2, Building2, User, MessageSquare, GripVertical } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { toast } from 'sonner'
import {
  getFeatureRequests,
  getFeatureRequestStats,
  updateFeatureRequest,
  type FeatureRequestWithUser,
  type FeatureRequestStats,
} from '@/api/endpoints/super-admin'
import { formatDateTime } from '@/lib/utils'

type StatusColumn = 'pending' | 'working' | 'done'

const COLUMNS: { id: StatusColumn; label: string; icon: React.ReactNode; color: string }[] = [
  { id: 'pending', label: 'Pending', icon: <Clock className="h-4 w-4" />, color: 'amber' },
  { id: 'working', label: 'Working', icon: <Loader2 className="h-4 w-4 animate-spin" />, color: 'blue' },
  { id: 'done', label: 'Done', icon: <CheckCircle2 className="h-4 w-4" />, color: 'green' },
]

function getCategoryIcon(category: string) {
  switch (category) {
    case 'bug':
      return <Bug className="h-3.5 w-3.5 text-red-500" />
    case 'feature':
      return <Lightbulb className="h-3.5 w-3.5 text-purple-500" />
    default:
      return null
  }
}

function getCategoryBadge(category: string) {
  switch (category) {
    case 'bug':
      return (
        <Badge variant="destructive" className="text-xs px-1.5 py-0">
          Bug
        </Badge>
      )
    case 'feature':
      return (
        <Badge variant="secondary" className="text-xs px-1.5 py-0 bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
          Feature
        </Badge>
      )
    default:
      return null
  }
}

interface FeatureRequestCardProps {
  request: FeatureRequestWithUser
  onDragStart: (e: React.DragEvent, request: FeatureRequestWithUser) => void
  onClick: () => void
}

function FeatureRequestCard({ request, onDragStart, onClick }: FeatureRequestCardProps) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, request)}
      onClick={onClick}
      className="bg-white border border-slate-200 rounded-lg p-3 cursor-pointer hover:border-slate-300 hover:shadow-sm transition-all group"
    >
      <div className="flex items-start gap-2">
        <GripVertical className="h-4 w-4 text-slate-400 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity cursor-grab" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {getCategoryIcon(request.category)}
            <span className="text-sm font-medium text-slate-900 truncate">{request.title}</span>
          </div>
          <p className="text-xs text-slate-600 line-clamp-2 mb-2">{request.description}</p>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <div className="flex items-center gap-1">
              <Building2 className="h-3 w-3" />
              <span className="truncate max-w-[80px]">{request.tenant_name || 'Unknown'}</span>
            </div>
            <span>·</span>
            <div className="flex items-center gap-1">
              <User className="h-3 w-3" />
              <span className="truncate max-w-[60px]">{request.user_name || 'Unknown'}</span>
            </div>
          </div>
          {request.admin_response && (
            <div className="flex items-center gap-1 mt-2 text-xs text-teal-600">
              <MessageSquare className="h-3 w-3" />
              <span>Has response</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface KanbanColumnProps {
  column: typeof COLUMNS[number]
  requests: FeatureRequestWithUser[]
  count: number
  onDragOver: (e: React.DragEvent) => void
  onDrop: (e: React.DragEvent, status: StatusColumn) => void
  onCardDragStart: (e: React.DragEvent, request: FeatureRequestWithUser) => void
  onCardClick: (request: FeatureRequestWithUser) => void
}

function KanbanColumn({ column, requests, count, onDragOver, onDrop, onCardDragStart, onCardClick }: KanbanColumnProps) {
  const [isDragOver, setIsDragOver] = useState(false)

  return (
    <div
      className={`flex flex-col min-w-[300px] max-w-[350px] bg-slate-50 rounded-lg border ${
        isDragOver ? 'border-teal-500 bg-teal-50/50' : 'border-slate-200'
      } transition-colors`}
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragOver(true)
        onDragOver(e)
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => {
        setIsDragOver(false)
        onDrop(e, column.id)
      }}
    >
      <div className={`px-4 py-3 border-b border-slate-200 bg-${column.color}-50`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`text-${column.color}-600`}>{column.icon}</span>
            <h3 className="font-semibold text-slate-900">{column.label}</h3>
          </div>
          <Badge variant="outline">
            {count}
          </Badge>
        </div>
      </div>
      <ScrollArea className="flex-1 p-3 max-h-[calc(100vh-350px)]">
        <div className="space-y-2">
          {requests.map((request) => (
            <FeatureRequestCard
              key={request.id}
              request={request}
              onDragStart={onCardDragStart}
              onClick={() => onCardClick(request)}
            />
          ))}
          {requests.length === 0 && (
            <div className="text-center py-8 text-slate-500 text-sm">
              No requests
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

interface DetailDialogProps {
  request: FeatureRequestWithUser | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onUpdate: (id: number, data: { status?: StatusColumn; admin_response?: string }) => void
  isUpdating: boolean
}

function DetailDialog({ request, open, onOpenChange, onUpdate, isUpdating }: DetailDialogProps) {
  const [adminResponse, setAdminResponse] = useState(request?.admin_response || '')
  const [status, setStatus] = useState<StatusColumn>(request?.status || 'pending')

  // Reset state when request changes
  useState(() => {
    if (request) {
      setAdminResponse(request.admin_response || '')
      setStatus(request.status)
    }
  })

  if (!request) return null

  const handleSave = () => {
    const updates: { status?: StatusColumn; admin_response?: string } = {}
    if (status !== request.status) {
      updates.status = status
    }
    if (adminResponse !== (request.admin_response || '')) {
      updates.admin_response = adminResponse
    }
    if (Object.keys(updates).length > 0) {
      onUpdate(request.id, updates)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <div className="flex items-center gap-2">
            {getCategoryBadge(request.category)}
            <DialogTitle>{request.title}</DialogTitle>
          </div>
          <DialogDescription>
            Submitted by {request.user_name} ({request.user_email}) from {request.tenant_name}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div>
            <h4 className="text-sm font-medium text-slate-700 mb-2">Description</h4>
            <p className="text-sm text-slate-600 bg-slate-50 rounded p-3 border border-slate-200">{request.description}</p>
          </div>

          <div>
            <h4 className="text-sm font-medium text-slate-700 mb-2">Status</h4>
            <div className="flex gap-2">
              {COLUMNS.map((col) => (
                <Button
                  key={col.id}
                  variant={status === col.id ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatus(col.id)}
                  className={status === col.id
                    ? `bg-${col.color}-600 hover:bg-${col.color}-700 text-white`
                    : ''}
                >
                  {col.icon}
                  <span className="ml-1">{col.label}</span>
                </Button>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-slate-700 mb-2">Admin Response (visible to user)</h4>
            <Textarea
              value={adminResponse}
              onChange={(e) => setAdminResponse(e.target.value)}
              placeholder="Add a response that the user will see..."
              rows={3}
            />
          </div>

          <div className="text-xs text-slate-500">
            <p>Created: {formatDateTime(request.created_at)}</p>
            {request.responded_at && (
              <p>Last response: {formatDateTime(request.responded_at)}</p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isUpdating} className="bg-teal-600 hover:bg-teal-700 text-white">
            {isUpdating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function FeatureRequestsKanban() {
  const queryClient = useQueryClient()
  const [selectedRequest, setSelectedRequest] = useState<FeatureRequestWithUser | null>(null)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [draggedRequest, setDraggedRequest] = useState<FeatureRequestWithUser | null>(null)

  // Fetch all requests
  const { data: requestsData, isLoading } = useQuery({
    queryKey: ['superAdminFeatureRequests'],
    queryFn: () => getFeatureRequests({ limit: 500 }),
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['superAdminFeatureRequestStats'],
    queryFn: getFeatureRequestStats,
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { status?: StatusColumn; admin_response?: string } }) =>
      updateFeatureRequest(id, data),
    onSuccess: () => {
      toast.success('Request updated successfully')
      queryClient.invalidateQueries({ queryKey: ['superAdminFeatureRequests'] })
      queryClient.invalidateQueries({ queryKey: ['superAdminFeatureRequestStats'] })
      setDetailDialogOpen(false)
    },
    onError: () => {
      toast.error('Failed to update request')
    },
  })

  const handleDragStart = (e: React.DragEvent, request: FeatureRequestWithUser) => {
    setDraggedRequest(request)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: React.DragEvent, newStatus: StatusColumn) => {
    e.preventDefault()
    if (draggedRequest && draggedRequest.status !== newStatus) {
      updateMutation.mutate({
        id: draggedRequest.id,
        data: { status: newStatus },
      })
    }
    setDraggedRequest(null)
  }

  const handleCardClick = (request: FeatureRequestWithUser) => {
    setSelectedRequest(request)
    setDetailDialogOpen(true)
  }

  const handleUpdate = (id: number, data: { status?: StatusColumn; admin_response?: string }) => {
    updateMutation.mutate({ id, data })
  }

  // Group requests by status
  const requestsByStatus = {
    pending: requestsData?.items.filter((r) => r.status === 'pending') || [],
    working: requestsData?.items.filter((r) => r.status === 'working') || [],
    done: requestsData?.items.filter((r) => r.status === 'done') || [],
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-teal-600" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Stats Summary */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Card className="bg-white border-slate-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">Total</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
            </CardContent>
          </Card>
          <Card className="bg-amber-50 border-amber-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-amber-700">Pending</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-amber-600">{stats.pending}</p>
            </CardContent>
          </Card>
          <Card className="bg-blue-50 border-blue-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-blue-700">Working</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-blue-600">{stats.working}</p>
            </CardContent>
          </Card>
          <Card className="bg-green-50 border-green-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-green-700">Done</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">{stats.done}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Kanban Board */}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {COLUMNS.map((column) => (
          <KanbanColumn
            key={column.id}
            column={column}
            requests={requestsByStatus[column.id]}
            count={requestsByStatus[column.id].length}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onCardDragStart={handleDragStart}
            onCardClick={handleCardClick}
          />
        ))}
      </div>

      {/* Detail Dialog */}
      <DetailDialog
        request={selectedRequest}
        open={detailDialogOpen}
        onOpenChange={setDetailDialogOpen}
        onUpdate={handleUpdate}
        isUpdating={updateMutation.isPending}
      />
    </div>
  )
}
