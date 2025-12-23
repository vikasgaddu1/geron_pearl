import { useState, useCallback, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ClipboardCheck, RefreshCw, Users, CheckCircle, MessageSquare, Edit, Trash2, Send, X } from 'lucide-react'
import { toast } from 'sonner'
import { reportingEffortsApi, trackerApi, trackerCommentsApi, usersApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
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
import { Badge } from '@/components/ui/badge'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { StatusBadge } from '@/components/common/StatusBadge'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { DataTable, ColumnDef } from '@/components/common/DataTable'
import { TooltipWrapper } from '@/components/common/TooltipWrapper'
import { HelpIcon } from '@/components/common/HelpIcon'
import { useWebSocketRefresh } from '@/hooks/useWebSocket'
import { formatDate, formatDateTime } from '@/lib/utils'
import type { ReportingEffortItemTracker, TrackerStatus, TrackerComment, CommentType, Priority } from '@/types'

const TRACKER_STATUSES: TrackerStatus[] = ['not_started', 'in_progress', 'completed', 'on_hold', 'failed']
const PRIORITIES: Priority[] = ['critical', 'high', 'medium', 'low']
const COMMENT_TYPES: CommentType[] = ['GENERAL', 'PROGRAMMING', 'BIOSTAT', 'QUESTION', 'ISSUE', 'RESPONSE']

export function TrackerManagement() {
  const queryClient = useQueryClient()
  const [selectedEffortId, setSelectedEffortId] = useState<string>('')
  const [activeTab, setActiveTab] = useState('tlf')
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())
  const [bulkAssignOpen, setBulkAssignOpen] = useState(false)
  const [bulkStatusOpen, setBulkStatusOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [commentDialogOpen, setCommentDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedTracker, setSelectedTracker] = useState<ReportingEffortItemTracker | null>(null)
  const [bulkData, setBulkData] = useState({ programmerId: '', status: 'in_progress' as TrackerStatus, assignmentType: 'primary' as 'primary' | 'qc' })
  const [editFormData, setEditFormData] = useState({
    production_programmer_id: '',
    qc_programmer_id: '',
    production_status: 'not_started' as TrackerStatus,
    qc_status: 'not_started' as TrackerStatus,
    priority: 'medium' as Priority,
    due_date: '',
    qc_completion_date: '',
  })
  const [newComment, setNewComment] = useState({ text: '', type: 'GENERAL' as CommentType })

  // Queries
  const { data: efforts = [], isLoading: effortsLoading } = useQuery({
    queryKey: ['reporting-efforts'],
    queryFn: reportingEffortsApi.getAll,
  })

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.getAll,
  })

  const { data: trackers = [], isLoading: trackersLoading } = useQuery({
    queryKey: ['trackers', selectedEffortId],
    queryFn: () => (selectedEffortId ? trackerApi.getByEffortBulk(Number(selectedEffortId)) : Promise.resolve([])),
    enabled: !!selectedEffortId,
  })

  const { data: comments = [], refetch: refetchComments } = useQuery({
    queryKey: ['tracker-comments', selectedTracker?.id],
    queryFn: () => (selectedTracker ? trackerCommentsApi.getThreaded(selectedTracker.id) : Promise.resolve([])),
    enabled: !!selectedTracker && commentDialogOpen,
  })

  // WebSocket refresh
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
  }, [queryClient, selectedEffortId])

  useWebSocketRefresh(['reporting_effort_tracker', 'comment'], refetch)

  // Mutations
  const bulkAssign = useMutation({
    mutationFn: trackerApi.bulkAssign,
    onSuccess: (result) => {
      toast.success(`Updated ${result.updated} trackers`)
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setBulkAssignOpen(false)
      setSelectedRows(new Set())
    },
    onError: () => toast.error('Failed to assign programmers'),
  })

  const bulkStatusUpdate = useMutation({
    mutationFn: trackerApi.bulkStatusUpdate,
    onSuccess: (result) => {
      toast.success(`Updated ${result.updated} trackers`)
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setBulkStatusOpen(false)
      setSelectedRows(new Set())
    },
    onError: () => toast.error('Failed to update status'),
  })

  const updateTracker = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      trackerApi.update(id, data as never),
    onSuccess: () => {
      toast.success('Tracker updated successfully')
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setEditDialogOpen(false)
    },
    onError: () => toast.error('Failed to update tracker'),
  })

  const deleteTracker = useMutation({
    mutationFn: trackerApi.delete,
    onSuccess: () => {
      toast.success('Tracker deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setSelectedTracker(null)
    },
    onError: () => toast.error('Failed to delete tracker'),
  })

  const createComment = useMutation({
    mutationFn: trackerCommentsApi.create,
    onSuccess: () => {
      toast.success('Comment added')
      refetchComments()
      setNewComment({ text: '', type: 'GENERAL' })
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
    },
    onError: () => toast.error('Failed to add comment'),
  })

  const resolveComment = useMutation({
    mutationFn: (commentId: number) => trackerCommentsApi.resolve(commentId),
    onSuccess: () => {
      toast.success('Comment resolved')
      refetchComments()
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
    },
    onError: () => toast.error('Failed to resolve comment'),
  })

  // Filter trackers by tab (TLF vs SDTM vs ADaM)
  const filterByTab = (tracker: ReportingEffortItemTracker) => {
    const subtype = tracker.item_subtype?.toLowerCase()
    if (activeTab === 'tlf') return ['table', 'listing', 'figure'].includes(subtype || '')
    if (activeTab === 'sdtm') return subtype === 'sdtm'
    if (activeTab === 'adam') return subtype === 'adam'
    return true
  }

  const filteredTrackers = useMemo(() => trackers.filter(filterByTab), [trackers, activeTab])

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedRows(new Set(filteredTrackers.map((t) => t.id)))
    } else {
      setSelectedRows(new Set())
    }
  }

  const handleSelectRow = (id: number, checked: boolean) => {
    const newSelected = new Set(selectedRows)
    if (checked) {
      newSelected.add(id)
    } else {
      newSelected.delete(id)
    }
    setSelectedRows(newSelected)
  }

  const handleBulkAssign = () => {
    bulkAssign.mutate({
      tracker_ids: Array.from(selectedRows),
      programmer_id: Number(bulkData.programmerId),
      assignment_type: bulkData.assignmentType,
    })
  }

  const handleBulkStatus = () => {
    bulkStatusUpdate.mutate({
      tracker_ids: Array.from(selectedRows),
      status: bulkData.status,
      status_type: bulkData.assignmentType === 'primary' ? 'production' : 'qc',
    })
  }

  const handleEdit = (tracker: ReportingEffortItemTracker) => {
    setSelectedTracker(tracker)
    setEditFormData({
      production_programmer_id: tracker.production_programmer_id?.toString() || '',
      qc_programmer_id: tracker.qc_programmer_id?.toString() || '',
      production_status: tracker.production_status || 'not_started',
      qc_status: tracker.qc_status || 'not_started',
      priority: (tracker.priority as Priority) || 'medium',
      due_date: tracker.due_date || '',
      qc_completion_date: tracker.qc_completion_date || '',
    })
    setEditDialogOpen(true)
  }

  const handleEditSubmit = () => {
    if (!selectedTracker) return
    updateTracker.mutate({
      id: selectedTracker.id,
      data: {
        production_programmer_id: editFormData.production_programmer_id ? Number(editFormData.production_programmer_id) : null,
        qc_programmer_id: editFormData.qc_programmer_id ? Number(editFormData.qc_programmer_id) : null,
        production_status: editFormData.production_status,
        qc_status: editFormData.qc_status,
        priority: editFormData.priority,
        due_date: editFormData.due_date || null,
        qc_completion_date: editFormData.qc_completion_date || null,
      },
    })
  }

  const handleOpenComments = (tracker: ReportingEffortItemTracker) => {
    setSelectedTracker(tracker)
    setCommentDialogOpen(true)
  }

  const handleAddComment = () => {
    if (!selectedTracker || !newComment.text.trim()) return
    createComment.mutate({
      tracker_id: selectedTracker.id,
      comment_text: newComment.text.trim(),
      comment_type: newComment.type,
    })
  }

  const handleDelete = (tracker: ReportingEffortItemTracker) => {
    setSelectedTracker(tracker)
    setDeleteDialogOpen(true)
  }

  // All users can be assigned as programmers
  const programmers = users

  const getProgrammerName = (id?: number) => {
    if (!id) return '-'
    const user = users.find((u) => u.id === id)
    return user?.username || '-'
  }

  // Define table columns
  const columns: ColumnDef<ReportingEffortItemTracker>[] = [
    {
      id: 'select',
      header: 'Select',
      accessorKey: 'id',
      filterType: 'none',
      enableSorting: false,
      cell: (_, tracker) => (
        <Checkbox
          checked={selectedRows.has(tracker.id)}
          onCheckedChange={(checked) => handleSelectRow(tracker.id, !!checked)}
          onClick={(e) => e.stopPropagation()}
        />
      ),
    },
    {
      id: 'item_code',
      header: 'Item Code',
      accessorKey: 'item_code',
      filterType: 'text',
      helpText: 'Unique identifier for the reporting item. Supports wildcard (*) and regex patterns.',
      cell: (value) => <span className="font-medium">{value}</span>,
    },
    {
      id: 'item_description',
      header: 'Description',
      accessorKey: 'item_description',
      filterType: 'text',
      helpText: 'Description of the reporting item output.',
      cell: (value) => <span className="max-w-xs truncate block">{value || '-'}</span>,
    },
    {
      id: 'production_programmer',
      header: 'Prod Programmer',
      accessorKey: 'production_programmer_id',
      filterType: 'select',
      filterOptions: users.map(u => u.username),
      helpText: 'Programmer assigned to produce this output.',
      cell: (value) => getProgrammerName(value as number),
    },
    {
      id: 'production_status',
      header: 'Prod Status',
      accessorKey: 'production_status',
      filterType: 'select',
      filterOptions: TRACKER_STATUSES,
      helpText: 'Current status of production work.',
      cell: (value) => <StatusBadge status={value as TrackerStatus} />,
    },
    {
      id: 'qc_programmer',
      header: 'QC Programmer',
      accessorKey: 'qc_programmer_id',
      filterType: 'select',
      filterOptions: users.map(u => u.username),
      helpText: 'Programmer assigned to QC this output.',
      cell: (value) => getProgrammerName(value as number),
    },
    {
      id: 'qc_status',
      header: 'QC Status',
      accessorKey: 'qc_status',
      filterType: 'select',
      filterOptions: TRACKER_STATUSES,
      helpText: 'Current status of QC work.',
      cell: (value) => <StatusBadge status={value as TrackerStatus} />,
    },
    {
      id: 'due_date',
      header: 'Due Date',
      accessorKey: 'due_date',
      filterType: 'date',
      helpText: 'Target completion date for this output.',
      cell: (value) => value ? formatDate(value as string) : '-',
    },
    {
      id: 'qc_completion_date',
      header: 'QC Completion',
      accessorKey: 'qc_completion_date',
      filterType: 'date',
      helpText: 'Date when QC was completed.',
      cell: (value) => value ? formatDate(value as string) : '-',
    },
    {
      id: 'comments',
      header: 'Comments',
      accessorKey: 'comment_count',
      filterType: 'none',
      enableSorting: false,
      cell: (_, tracker) => (
        <TooltipWrapper 
          content={`${tracker.comment_count || 0} total comments, ${tracker.unresolved_comment_count || 0} unresolved`}
        >
          <Button variant="ghost" size="sm" onClick={() => handleOpenComments(tracker)}>
            <MessageSquare className="h-4 w-4" />
            {tracker.comment_count ? (
              <Badge variant="secondary" className="ml-1">{tracker.comment_count}</Badge>
            ) : null}
            {tracker.unresolved_comment_count ? (
              <Badge variant="destructive" className="ml-1">{tracker.unresolved_comment_count}</Badge>
            ) : null}
          </Button>
        </TooltipWrapper>
      ),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessorKey: 'id',
      filterType: 'none',
      enableSorting: false,
      cell: (_, tracker) => (
        <div className="flex justify-end gap-1">
          <TooltipWrapper content="Edit tracker assignments and status">
            <Button variant="ghost" size="icon" onClick={() => handleEdit(tracker)}>
              <Edit className="h-4 w-4" />
            </Button>
          </TooltipWrapper>
          <TooltipWrapper content="Delete tracker">
            <Button variant="ghost" size="icon" onClick={() => handleDelete(tracker)}>
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </TooltipWrapper>
        </div>
      ),
    },
  ]

  if (effortsLoading) {
    return <PageLoader text="Loading..." />
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div className="flex items-center gap-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                <ClipboardCheck className="h-5 w-5 text-primary" />
                Tracker Management
              </CardTitle>
              <CardDescription>
                Manage programmer assignments and status tracking
              </CardDescription>
            </div>
            <HelpIcon
              title="Tracker Management"
              content={
                <div className="space-y-2">
                  <p>Track production and QC progress for reporting outputs.</p>
                  <div className="space-y-1">
                    <p className="font-semibold text-sm">Features:</p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li>Assign programmers to outputs</li>
                      <li>Track production and QC status</li>
                      <li>Set due dates and priorities</li>
                      <li>Manage comments and discussions</li>
                      <li>Bulk operations for efficiency</li>
                    </ul>
                  </div>
                </div>
              }
            />
          </div>
          <div className="flex gap-2">
            <TooltipWrapper content="Refresh tracker data">
              <Button variant="outline" size="sm" onClick={refetch} disabled={!selectedEffortId}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </TooltipWrapper>
            {selectedRows.size > 0 && (
              <>
                <TooltipWrapper content={`Assign programmer to ${selectedRows.size} selected trackers`}>
                  <Button variant="outline" size="sm" onClick={() => setBulkAssignOpen(true)}>
                    <Users className="h-4 w-4 mr-2" />
                    Assign ({selectedRows.size})
                  </Button>
                </TooltipWrapper>
                <TooltipWrapper content={`Update status for ${selectedRows.size} selected trackers`}>
                  <Button variant="outline" size="sm" onClick={() => setBulkStatusOpen(true)}>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Update Status
                  </Button>
                </TooltipWrapper>
              </>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <div className="w-80">
              <Label>Reporting Effort</Label>
              <Select value={selectedEffortId} onValueChange={(v) => { setSelectedEffortId(v); setSelectedRows(new Set()) }}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a reporting effort" />
                </SelectTrigger>
                <SelectContent>
                  {efforts.map((effort) => (
                    <SelectItem key={effort.id} value={String(effort.id)}>
                      {effort.database_release_label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {!selectedEffortId ? (
            <EmptyState
              icon={ClipboardCheck}
              title="Select a reporting effort"
              description="Choose a reporting effort to view and manage its trackers."
            />
          ) : trackersLoading ? (
            <PageLoader text="Loading trackers..." />
          ) : (
            <Tabs value={activeTab} onValueChange={(v) => { setActiveTab(v); setSelectedRows(new Set()) }}>
              <TabsList className="mb-4">
                <TabsTrigger value="tlf">
                  TLF Tracker
                  <Badge variant="secondary" className="ml-2">
                    {trackers.filter((t) => ['table', 'listing', 'figure'].includes(t.item_subtype?.toLowerCase() || '')).length}
                  </Badge>
                </TabsTrigger>
                <TabsTrigger value="sdtm">
                  SDTM Tracker
                  <Badge variant="secondary" className="ml-2">
                    {trackers.filter((t) => t.item_subtype?.toLowerCase() === 'sdtm').length}
                  </Badge>
                </TabsTrigger>
                <TabsTrigger value="adam">
                  ADaM Tracker
                  <Badge variant="secondary" className="ml-2">
                    {trackers.filter((t) => t.item_subtype?.toLowerCase() === 'adam').length}
                  </Badge>
                </TabsTrigger>
              </TabsList>

              {['tlf', 'sdtm', 'adam'].map((tab) => (
                <TabsContent key={tab} value={tab}>
                  {filteredTrackers.length === 0 ? (
                    <EmptyState
                      icon={ClipboardCheck}
                      title="No trackers found"
                      description="No items in this tracker."
                    />
                  ) : (
                    <DataTable data={filteredTrackers} columns={columns} />
                  )}
                </TabsContent>
              ))}
            </Tabs>
          )}
        </CardContent>
      </Card>

      {/* Edit Tracker Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Tracker</DialogTitle>
            <DialogDescription>
              Update tracker for {selectedTracker?.item_code}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>Production Programmer</Label>
                <Select
                  value={editFormData.production_programmer_id || 'none'}
                  onValueChange={(v) => setEditFormData((prev) => ({ ...prev, production_programmer_id: v === 'none' ? '' : v }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select programmer" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">-- Unassigned --</SelectItem>
                    {programmers.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>{p.username}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>QC Programmer</Label>
                <Select
                  value={editFormData.qc_programmer_id || 'none'}
                  onValueChange={(v) => setEditFormData((prev) => ({ ...prev, qc_programmer_id: v === 'none' ? '' : v }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select programmer" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">-- Unassigned --</SelectItem>
                    {programmers.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>{p.username}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>Production Status</Label>
                <Select
                  value={editFormData.production_status}
                  onValueChange={(v: TrackerStatus) => setEditFormData((prev) => ({ ...prev, production_status: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TRACKER_STATUSES.map((s) => (
                      <SelectItem key={s} value={s}>{s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>QC Status</Label>
                <Select
                  value={editFormData.qc_status}
                  onValueChange={(v: TrackerStatus) => setEditFormData((prev) => ({ ...prev, qc_status: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TRACKER_STATUSES.map((s) => (
                      <SelectItem key={s} value={s}>{s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="grid gap-2">
                <Label>Priority</Label>
                <Select
                  value={editFormData.priority}
                  onValueChange={(v: Priority) => setEditFormData((prev) => ({ ...prev, priority: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PRIORITIES.map((p) => (
                      <SelectItem key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>Due Date</Label>
                <Input
                  type="date"
                  value={editFormData.due_date}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, due_date: e.target.value }))}
                />
              </div>
              <div className="grid gap-2">
                <Label>QC Completion Date</Label>
                <Input
                  type="date"
                  value={editFormData.qc_completion_date}
                  onChange={(e) => setEditFormData((prev) => ({ ...prev, qc_completion_date: e.target.value }))}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleEditSubmit}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Comments Dialog */}
      <Dialog open={commentDialogOpen} onOpenChange={setCommentDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Comments for {selectedTracker?.item_code}
            </DialogTitle>
            <DialogDescription>
              View and add comments for this tracker item
            </DialogDescription>
          </DialogHeader>
          
          {/* Comment List */}
          <ScrollArea className="h-[300px] pr-4">
            {comments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No comments yet. Add the first comment below.
              </div>
            ) : (
              <div className="space-y-4">
                {comments.map((comment) => (
                  <CommentItem 
                    key={comment.id} 
                    comment={comment} 
                    onResolve={() => resolveComment.mutate(comment.id)}
                  />
                ))}
              </div>
            )}
          </ScrollArea>

          {/* Add Comment Form */}
          <div className="border-t pt-4 mt-4">
            <div className="flex gap-2 mb-2">
              <Select
                value={newComment.type}
                onValueChange={(v: CommentType) => setNewComment((prev) => ({ ...prev, type: v }))}
              >
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {COMMENT_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2">
              <Textarea
                placeholder="Add a comment..."
                value={newComment.text}
                onChange={(e) => setNewComment((prev) => ({ ...prev, text: e.target.value }))}
                className="flex-1"
                rows={2}
              />
              <Button onClick={handleAddComment} disabled={!newComment.text.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Bulk Assign Dialog */}
      <Dialog open={bulkAssignOpen} onOpenChange={setBulkAssignOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bulk Assign Programmer</DialogTitle>
            <DialogDescription>
              Assign a programmer to {selectedRows.size} selected tracker(s).
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Assignment Type</Label>
              <Select
                value={bulkData.assignmentType}
                onValueChange={(v: 'primary' | 'qc') => setBulkData((prev) => ({ ...prev, assignmentType: v }))}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="primary">Production Programmer</SelectItem>
                  <SelectItem value="qc">QC Programmer</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>Programmer</Label>
              <Select
                value={bulkData.programmerId}
                onValueChange={(v) => setBulkData((prev) => ({ ...prev, programmerId: v }))}
              >
                <SelectTrigger><SelectValue placeholder="Select programmer" /></SelectTrigger>
                <SelectContent>
                  {programmers.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>{p.username}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkAssignOpen(false)}>Cancel</Button>
            <Button onClick={handleBulkAssign} disabled={!bulkData.programmerId}>Assign</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Status Dialog */}
      <Dialog open={bulkStatusOpen} onOpenChange={setBulkStatusOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bulk Update Status</DialogTitle>
            <DialogDescription>
              Update status for {selectedRows.size} selected tracker(s).
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Status Type</Label>
              <Select
                value={bulkData.assignmentType}
                onValueChange={(v: 'primary' | 'qc') => setBulkData((prev) => ({ ...prev, assignmentType: v }))}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="primary">Production Status</SelectItem>
                  <SelectItem value="qc">QC Status</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>New Status</Label>
              <Select
                value={bulkData.status}
                onValueChange={(v: TrackerStatus) => setBulkData((prev) => ({ ...prev, status: v }))}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TRACKER_STATUSES.map((s) => (
                    <SelectItem key={s} value={s}>{s.replace(/_/g, ' ')}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkStatusOpen(false)}>Cancel</Button>
            <Button onClick={handleBulkStatus}>Update Status</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Tracker?"
        description={`Are you sure you want to delete the tracker for "${selectedTracker?.item_code}"?`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={() => { if (selectedTracker) deleteTracker.mutate(selectedTracker.id); setDeleteDialogOpen(false) }}
      />
    </div>
  )
}

// Comment Item Component
function CommentItem({ comment, onResolve }: { comment: TrackerComment; onResolve: () => void }) {
  return (
    <div className={`p-3 rounded-lg border ${comment.is_resolved ? 'bg-muted/50 opacity-70' : 'bg-card'}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-sm">{comment.user?.username || 'Unknown'}</span>
            <Badge variant="outline" className="text-xs">{comment.comment_type}</Badge>
            {comment.is_resolved && <Badge variant="secondary" className="text-xs">Resolved</Badge>}
            <span className="text-xs text-muted-foreground">{formatDateTime(comment.created_at)}</span>
          </div>
          <p className="text-sm">{comment.comment_text}</p>
        </div>
        {!comment.is_resolved && (
          <Button variant="ghost" size="sm" onClick={onResolve}>
            <X className="h-4 w-4 mr-1" />
            Resolve
          </Button>
        )}
      </div>
      {/* Nested Replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="ml-4 mt-2 space-y-2 border-l-2 pl-3">
          {comment.replies.map((reply) => (
            <CommentItem key={reply.id} comment={reply} onResolve={() => {}} />
          ))}
        </div>
      )}
    </div>
  )
}


