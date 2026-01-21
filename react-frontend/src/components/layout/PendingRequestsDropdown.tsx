import { useEffect, useState } from 'react'
import { UserCheck, UserPlus, Check, X, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { useAccessRequestStore } from '@/stores/accessRequestStore'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'
import type { AccessRequest } from '@/types'

function getRequestTypeLabel(type: string) {
  switch (type) {
    case 'EDITOR':
      return 'Editor access'
    case 'RESPONSIBLE_USER':
      return 'Responsible User'
    default:
      return type
  }
}

function getRequestTypeIcon(type: string) {
  switch (type) {
    case 'EDITOR':
      return <UserPlus className="h-4 w-4 text-blue-500" />
    case 'RESPONSIBLE_USER':
      return <UserCheck className="h-4 w-4 text-amber-500" />
    default:
      return <Users className="h-4 w-4" />
  }
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function RequestItem({
  request,
  onApprove,
  onDeny,
}: {
  request: AccessRequest
  onApprove: (id: number) => void
  onDeny: (id: number) => void
}) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg transition-colors',
        'bg-primary/5 border-l-2 border-primary'
      )}
    >
      <div className="flex-shrink-0 mt-1">{getRequestTypeIcon(request.request_type)}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground">
          {request.requester_username}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5">
          Requests <span className="font-medium">{getRequestTypeLabel(request.request_type)}</span> for{' '}
          <span className="font-medium">{request.study_label}</span>
        </p>
        {request.request_reason && (
          <p className="text-xs text-muted-foreground mt-1 italic line-clamp-2">
            "{request.request_reason}"
          </p>
        )}
        <span className="text-[10px] text-muted-foreground mt-1 block">
          {formatTimeAgo(request.created_at)}
        </span>
      </div>
      <div className="flex flex-col gap-1 flex-shrink-0">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-green-600 hover:text-green-700 hover:bg-green-100"
          onClick={(e) => {
            e.stopPropagation()
            onApprove(request.id)
          }}
          title="Approve request"
        >
          <Check className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-red-600 hover:text-red-700 hover:bg-red-100"
          onClick={(e) => {
            e.stopPropagation()
            onDeny(request.id)
          }}
          title="Deny request"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

export function PendingRequestsDropdown() {
  const { isAuthenticated, currentUser, hasResponsibleAccess } = useAuthStore()
  const {
    pendingRequests,
    pendingCount,
    isLoading,
    isDropdownOpen,
    setDropdownOpen,
    fetchPendingRequests,
    fetchPendingCount,
    approveRequest,
    denyRequest,
  } = useAccessRequestStore()

  // State for deny dialog
  const [denyDialogOpen, setDenyDialogOpen] = useState(false)
  const [selectedRequestId, setSelectedRequestId] = useState<number | null>(null)
  const [denialReason, setDenialReason] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)

  // Only show to admins or users with responsible access
  const canApprove = currentUser?.is_admin || hasResponsibleAccess()

  // Fetch count when authenticated and has approval permissions
  useEffect(() => {
    if (isAuthenticated && canApprove) {
      fetchPendingCount()
    }
  }, [isAuthenticated, canApprove, fetchPendingCount])

  // Fetch full requests when dropdown opens
  useEffect(() => {
    if (isDropdownOpen && isAuthenticated && canApprove) {
      fetchPendingRequests()
    }
  }, [isDropdownOpen, isAuthenticated, canApprove, fetchPendingRequests])

  if (!isAuthenticated || !canApprove) {
    return null
  }

  const handleApprove = async (requestId: number) => {
    setIsProcessing(true)
    try {
      await approveRequest(requestId)
    } catch (error) {
      console.error('Failed to approve request:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDenyClick = (requestId: number) => {
    setSelectedRequestId(requestId)
    setDenialReason('')
    setDenyDialogOpen(true)
  }

  const handleDenyConfirm = async () => {
    if (!selectedRequestId) return
    setIsProcessing(true)
    try {
      await denyRequest(selectedRequestId, denialReason || undefined)
      setDenyDialogOpen(false)
      setSelectedRequestId(null)
      setDenialReason('')
    } catch (error) {
      console.error('Failed to deny request:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <>
      <DropdownMenu open={isDropdownOpen} onOpenChange={setDropdownOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="relative">
            <Users className="h-5 w-5" />
            {pendingCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
                <Badge
                  className="relative h-4 min-w-4 px-1 text-[10px] font-bold rounded-full flex items-center justify-center bg-amber-500"
                >
                  {pendingCount > 99 ? '99+' : pendingCount}
                </Badge>
              </span>
            )}
          </Button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" className="w-96">
          <DropdownMenuLabel>
            <span>Access Requests</span>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />

          {isLoading ? (
            <div className="p-4 text-center text-sm text-muted-foreground">
              Loading requests...
            </div>
          ) : pendingRequests.length === 0 ? (
            <div className="p-4 text-center">
              <Users className="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
              <p className="text-sm text-muted-foreground">No pending requests</p>
              <p className="text-xs text-muted-foreground mt-1">
                All access requests have been handled.
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[400px]">
              <div className="space-y-1 p-1">
                {pendingRequests.map((request) => (
                  <div key={request.id} className="group">
                    <RequestItem
                      request={request}
                      onApprove={handleApprove}
                      onDeny={handleDenyClick}
                    />
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Deny Confirmation Dialog */}
      <Dialog open={denyDialogOpen} onOpenChange={setDenyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Deny Access Request</DialogTitle>
            <DialogDescription>
              Optionally provide a reason for denying this request. The requester will be notified.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="denial-reason">Reason (optional)</Label>
            <Textarea
              id="denial-reason"
              placeholder="Enter a reason for denial..."
              value={denialReason}
              onChange={(e) => setDenialReason(e.target.value)}
              className="mt-2"
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDenyDialogOpen(false)} disabled={isProcessing}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDenyConfirm} disabled={isProcessing}>
              {isProcessing ? 'Denying...' : 'Deny Request'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
