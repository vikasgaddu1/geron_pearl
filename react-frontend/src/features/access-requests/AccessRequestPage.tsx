import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  UserPlus,
  UserCheck,
  Check,
  X,
  Clock,
  Send,
  History,
  Search,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { studiesApi } from '@/api/endpoints/studies'
import { accessRequestsApi } from '@/api/endpoints/access-requests'
import { useAuthStore } from '@/stores/authStore'
import { formatDateTime, getErrorMessage } from '@/lib/utils'
import type { Study, AccessRequest, AccessRequestType, AccessRequestStatus } from '@/types'

function getStatusBadge(status: AccessRequestStatus) {
  switch (status) {
    case 'PENDING':
      return (
        <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
          <Clock className="h-3 w-3 mr-1" />
          Pending
        </Badge>
      )
    case 'APPROVED':
      return (
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
          <Check className="h-3 w-3 mr-1" />
          Approved
        </Badge>
      )
    case 'DENIED':
      return (
        <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
          <X className="h-3 w-3 mr-1" />
          Denied
        </Badge>
      )
    default:
      return <Badge variant="outline">{status}</Badge>
  }
}

function getRequestTypeLabel(type: AccessRequestType) {
  switch (type) {
    case 'EDITOR':
      return 'Editor'
    case 'RESPONSIBLE_USER':
      return 'Responsible User'
    default:
      return type
  }
}

function getRequestTypeIcon(type: AccessRequestType) {
  switch (type) {
    case 'EDITOR':
      return <UserPlus className="h-4 w-4 text-blue-500" />
    case 'RESPONSIBLE_USER':
      return <UserCheck className="h-4 w-4 text-amber-500" />
    default:
      return null
  }
}

export function AccessRequestPage() {
  const queryClient = useQueryClient()
  const { currentUser, isResponsibleForStudy } = useAuthStore()

  // State
  const [searchQuery, setSearchQuery] = useState('')
  const [requestDialogOpen, setRequestDialogOpen] = useState(false)
  const [selectedStudy, setSelectedStudy] = useState<Study | null>(null)
  const [requestType, setRequestType] = useState<AccessRequestType>('EDITOR')
  const [requestReason, setRequestReason] = useState('')

  // Queries
  const { data: studies = [], isLoading: studiesLoading } = useQuery({
    queryKey: ['studies'],
    queryFn: () => studiesApi.getAll(),
  })

  const { data: myRequestsData, isLoading: myRequestsLoading, refetch: refetchMyRequests } = useQuery({
    queryKey: ['access-requests', 'requester'],
    queryFn: () => accessRequestsApi.list('requester'),
  })

  const myRequests = myRequestsData?.requests || []

  // Mutations
  const createRequestMutation = useMutation({
    mutationFn: accessRequestsApi.create,
    onSuccess: () => {
      toast.success('Access request submitted', {
        description: 'Your request has been sent to the approvers.',
      })
      setRequestDialogOpen(false)
      setSelectedStudy(null)
      setRequestReason('')
      refetchMyRequests()
    },
    onError: (error) => {
      toast.error('Failed to submit request', {
        description: getErrorMessage(error),
      })
    },
  })

  // Filter studies based on search
  const filteredStudies = studies.filter((study) =>
    study.study_label.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Check if user already has pending request for study/type
  const hasPendingRequest = (studyId: number, type: AccessRequestType) => {
    return myRequests.some(
      (req) =>
        req.study_id === studyId && req.request_type === type && req.status === 'PENDING'
    )
  }

  // Check if user already has the access
  const hasAccess = (studyId: number, type: AccessRequestType) => {
    if (currentUser?.is_admin) return true
    if (type === 'RESPONSIBLE_USER') {
      return isResponsibleForStudy(studyId)
    }
    // For EDITOR, we don't have a quick check in the store, so we'll rely on backend validation
    return false
  }

  const handleRequestAccess = (study: Study) => {
    setSelectedStudy(study)
    setRequestType('EDITOR')
    setRequestReason('')
    setRequestDialogOpen(true)
  }

  const handleSubmitRequest = () => {
    if (!selectedStudy) return
    createRequestMutation.mutate({
      study_id: selectedStudy.id,
      request_type: requestType,
      request_reason: requestReason || undefined,
    })
  }

  if (currentUser?.is_admin) {
    return (
      <div className="container mx-auto py-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              Access Requests
            </CardTitle>
            <CardDescription>
              As a global administrator, you already have full access to all studies.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              You don't need to request access to any studies. Use the{' '}
              <span className="font-medium">Access Requests dropdown</span> in the navigation bar
              to manage pending requests from other users.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (studiesLoading || myRequestsLoading) {
    return <PageLoader message="Loading..." />
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Request Access</h1>
        <p className="text-muted-foreground">
          Request Editor or Responsible User access to studies
        </p>
      </div>

      <Tabs defaultValue="request" className="w-full">
        <TabsList>
          <TabsTrigger value="request" className="flex items-center gap-2">
            <Send className="h-4 w-4" />
            Request Access
          </TabsTrigger>
          <TabsTrigger value="history" className="flex items-center gap-2">
            <History className="h-4 w-4" />
            My Requests
            {myRequests.filter((r) => r.status === 'PENDING').length > 0 && (
              <Badge variant="secondary" className="ml-1">
                {myRequests.filter((r) => r.status === 'PENDING').length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="request" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Available Studies</CardTitle>
              <CardDescription>
                Select a study to request Editor or Responsible User access
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search studies..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>

              {filteredStudies.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No studies found matching your search.
                </p>
              ) : (
                <div className="border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Study</TableHead>
                        <TableHead>Your Access</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredStudies.map((study) => {
                        const isResponsible = isResponsibleForStudy(study.id)
                        const pendingEditor = hasPendingRequest(study.id, 'EDITOR')
                        const pendingResponsible = hasPendingRequest(study.id, 'RESPONSIBLE_USER')

                        return (
                          <TableRow key={study.id}>
                            <TableCell className="font-medium">{study.study_label}</TableCell>
                            <TableCell>
                              {isResponsible ? (
                                <Badge className="bg-amber-500">Responsible User</Badge>
                              ) : (
                                <Badge variant="outline">Viewer</Badge>
                              )}
                              {pendingEditor && (
                                <Badge variant="outline" className="ml-2 bg-amber-50 text-amber-700">
                                  Editor (Pending)
                                </Badge>
                              )}
                              {pendingResponsible && (
                                <Badge variant="outline" className="ml-2 bg-amber-50 text-amber-700">
                                  Responsible (Pending)
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRequestAccess(study)}
                                disabled={isResponsible && pendingEditor}
                              >
                                <UserPlus className="h-4 w-4 mr-2" />
                                Request Access
                              </Button>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>My Access Requests</CardTitle>
              <CardDescription>
                View the status of your submitted access requests
              </CardDescription>
            </CardHeader>
            <CardContent>
              {myRequests.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  You haven't submitted any access requests yet.
                </p>
              ) : (
                <div className="border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Study</TableHead>
                        <TableHead>Request Type</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Submitted</TableHead>
                        <TableHead>Resolved By</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {myRequests.map((request) => (
                        <TableRow key={request.id}>
                          <TableCell className="font-medium">{request.study_label}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {getRequestTypeIcon(request.request_type)}
                              {getRequestTypeLabel(request.request_type)}
                            </div>
                          </TableCell>
                          <TableCell>{getStatusBadge(request.status)}</TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {formatDateTime(request.created_at)}
                          </TableCell>
                          <TableCell>
                            {request.resolved_by_username ? (
                              <span className="text-sm">
                                {request.resolved_by_username}
                                {request.denial_reason && (
                                  <span className="block text-xs text-muted-foreground italic">
                                    "{request.denial_reason}"
                                  </span>
                                )}
                              </span>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Request Access Dialog */}
      <Dialog open={requestDialogOpen} onOpenChange={setRequestDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request Access</DialogTitle>
            <DialogDescription>
              Request access to <span className="font-medium">{selectedStudy?.study_label}</span>
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Access Type</Label>
              <Select
                value={requestType}
                onValueChange={(value) => setRequestType(value as AccessRequestType)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="EDITOR">
                    <div className="flex items-center gap-2">
                      <UserPlus className="h-4 w-4 text-blue-500" />
                      <div>
                        <span className="font-medium">Editor</span>
                        <span className="text-muted-foreground ml-2">- Edit assigned items</span>
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem
                    value="RESPONSIBLE_USER"
                    disabled={selectedStudy ? isResponsibleForStudy(selectedStudy.id) : false}
                  >
                    <div className="flex items-center gap-2">
                      <UserCheck className="h-4 w-4 text-amber-500" />
                      <div>
                        <span className="font-medium">Responsible User</span>
                        <span className="text-muted-foreground ml-2">- Full study management</span>
                      </div>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="reason">Reason (optional)</Label>
              <Textarea
                id="reason"
                placeholder="Explain why you need this access..."
                value={requestReason}
                onChange={(e) => setRequestReason(e.target.value)}
                rows={3}
              />
            </div>

            {selectedStudy && hasPendingRequest(selectedStudy.id, requestType) && (
              <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">
                You already have a pending request for {getRequestTypeLabel(requestType)} access
                to this study.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRequestDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitRequest}
              disabled={
                createRequestMutation.isPending ||
                (selectedStudy ? hasPendingRequest(selectedStudy.id, requestType) : false)
              }
            >
              {createRequestMutation.isPending ? 'Submitting...' : 'Submit Request'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
