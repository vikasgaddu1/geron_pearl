import { useState, useCallback, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ClipboardCheck, RefreshCw, Users, CheckCircle, MessageSquare, Edit, Trash2, Send, X, Tag, Plus, Reply, Filter } from 'lucide-react'
import { toast } from 'sonner'
import { reportingEffortsApi, trackerApi, trackerCommentsApi, trackerTagsApi, usersApi } from '@/api'
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Badge } from '@/components/ui/badge'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { StatusBadge } from '@/components/common/StatusBadge'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { DataTable, ColumnDef } from '@/components/common/DataTable'
import { TooltipWrapper } from '@/components/common/TooltipWrapper'
import { HelpIcon } from '@/components/common/HelpIcon'
import { useWebSocketRefresh } from '@/hooks/useWebSocket'
import { formatDate, formatDateTime, getErrorMessage } from '@/lib/utils'
import type { ReportingEffortItemTracker, TrackerStatus, TrackerComment, CommentType, Priority, TrackerTag, TrackerTagSummary } from '@/types'

const TRACKER_STATUSES: TrackerStatus[] = ['not_started', 'in_progress', 'completed', 'on_hold', 'failed']
const PRIORITIES: Priority[] = ['critical', 'high', 'medium', 'low']
// Simplified comment types for programmer/QC communication (backend only accepts programming/biostat)
const COMMENT_TYPES: { value: CommentType; label: string }[] = [
  { value: 'PROGRAMMING', label: 'Programmer' },
  { value: 'BIOSTAT', label: 'QC Programmer' },
]

// Preset colors for tags
const TAG_COLORS = [
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
]

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
  const [tagManageOpen, setTagManageOpen] = useState(false)
  const [bulkTagOpen, setBulkTagOpen] = useState(false)
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
  const [newComment, setNewComment] = useState({ text: '', type: 'PROGRAMMING' as CommentType, parentId: null as number | null })
  const [replyingTo, setReplyingTo] = useState<TrackerComment | null>(null)
  
  // Filter states
  const [commentFilter, setCommentFilter] = useState<'all' | 'has_comments' | 'has_unresolved'>('all')
  const [tagFilter, setTagFilter] = useState<number | null>(null)
  
  // Tag management state
  const [newTag, setNewTag] = useState({ name: '', color: '#3B82F6', description: '' })
  const [editingTag, setEditingTag] = useState<TrackerTag | null>(null)

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

  const { data: allTags = [], refetch: refetchTags } = useQuery({
    queryKey: ['tracker-tags'],
    queryFn: trackerTagsApi.getAll,
  })

  // WebSocket refresh
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
    queryClient.invalidateQueries({ queryKey: ['tracker-tags'] })
  }, [queryClient, selectedEffortId])

  useWebSocketRefresh(['reporting_effort_tracker', 'comment', 'tracker_tag'], refetch)

  // Mutations
  const bulkAssign = useMutation({
    mutationFn: trackerApi.bulkAssign,
    onSuccess: (result) => {
      toast.success(`Updated ${result.updated} trackers`)
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setBulkAssignOpen(false)
      setSelectedRows(new Set())
    },
    onError: (error) => toast.error(`Failed to assign programmers: ${getErrorMessage(error)}`),
  })

  const bulkStatusUpdate = useMutation({
    mutationFn: trackerApi.bulkStatusUpdate,
    onSuccess: (result) => {
      toast.success(`Updated ${result.updated} trackers`)
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setBulkStatusOpen(false)
      setSelectedRows(new Set())
    },
    onError: (error) => toast.error(`Failed to update status: ${getErrorMessage(error)}`),
  })

  const updateTracker = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      trackerApi.update(id, data as never),
    onSuccess: () => {
      toast.success('Tracker updated successfully')
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setEditDialogOpen(false)
    },
    onError: (error) => toast.error(`Failed to update tracker: ${getErrorMessage(error)}`),
  })

  const deleteTracker = useMutation({
    mutationFn: trackerApi.delete,
    onSuccess: () => {
      toast.success('Tracker deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setSelectedTracker(null)
    },
    onError: (error) => toast.error(`Failed to delete tracker: ${getErrorMessage(error)}`),
  })

  const createComment = useMutation({
    mutationFn: trackerCommentsApi.create,
    onSuccess: () => {
      toast.success('Comment added')
      refetchComments()
      setNewComment({ text: '', type: 'PROGRAMMING', parentId: null })
      setReplyingTo(null)
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
    },
    onError: (error) => toast.error(`Failed to add comment: ${getErrorMessage(error)}`),
  })

  const resolveComment = useMutation({
    mutationFn: (commentId: number) => trackerCommentsApi.resolve(commentId),
    onSuccess: () => {
      toast.success('Comment resolved')
      refetchComments()
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
    },
    onError: (error) => toast.error(`Failed to resolve comment: ${getErrorMessage(error)}`),
  })

  // Tag mutations
  const createTag = useMutation({
    mutationFn: trackerTagsApi.create,
    onSuccess: () => {
      toast.success('Tag created')
      refetchTags()
      setNewTag({ name: '', color: '#3B82F6', description: '' })
    },
    onError: (error) => toast.error(`Failed to create tag: ${getErrorMessage(error)}`),
  })

  const updateTag = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { name?: string; color?: string; description?: string } }) =>
      trackerTagsApi.update(id, data),
    onSuccess: () => {
      toast.success('Tag updated')
      refetchTags()
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setEditingTag(null)
    },
    onError: (error) => toast.error(`Failed to update tag: ${getErrorMessage(error)}`),
  })

  const deleteTag = useMutation({
    mutationFn: trackerTagsApi.delete,
    onSuccess: () => {
      toast.success('Tag deleted')
      refetchTags()
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
    },
    onError: (error) => toast.error(`Failed to delete tag: ${getErrorMessage(error)}`),
  })

  const assignTag = useMutation({
    mutationFn: ({ trackerId, tagId }: { trackerId: number; tagId: number }) =>
      trackerTagsApi.assignTag(trackerId, tagId),
    onSuccess: () => {
      toast.success('Tag assigned')
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
    },
    onError: (error) => toast.error(`Failed to assign tag: ${getErrorMessage(error)}`),
  })

  const removeTag = useMutation({
    mutationFn: ({ trackerId, tagId }: { trackerId: number; tagId: number }) =>
      trackerTagsApi.removeTag(trackerId, tagId),
    onSuccess: () => {
      toast.success('Tag removed')
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
    },
    onError: (error) => toast.error(`Failed to remove tag: ${getErrorMessage(error)}`),
  })

  const bulkAssignTag = useMutation({
    mutationFn: trackerTagsApi.bulkAssign,
    onSuccess: (result) => {
      toast.success(`Tag assigned to ${result.affected_count} trackers`)
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setBulkTagOpen(false)
      setSelectedRows(new Set())
    },
    onError: (error) => toast.error(`Failed to assign tags: ${getErrorMessage(error)}`),
  })

  // Filter trackers by tab (TLF vs SDTM vs ADaM)
  const filterByTab = (tracker: ReportingEffortItemTracker) => {
    const subtype = tracker.item_subtype?.toLowerCase()
    if (activeTab === 'tlf') return ['table', 'listing', 'figure'].includes(subtype || '')
    if (activeTab === 'sdtm') return subtype === 'sdtm'
    if (activeTab === 'adam') return subtype === 'adam'
    return true
  }

  // Apply all filters
  const filteredTrackers = useMemo(() => {
    let result = trackers.filter(filterByTab)
    
    // Comment filter
    if (commentFilter === 'has_comments') {
      result = result.filter(t => (t.unresolved_comment_count || 0) > 0 || (t.comment_count || 0) > 0)
    } else if (commentFilter === 'has_unresolved') {
      result = result.filter(t => (t.unresolved_comment_count || 0) > 0)
    }
    
    // Tag filter
    if (tagFilter !== null) {
      result = result.filter(t => t.tags?.some(tag => tag.id === tagFilter))
    }
    
    return result
  }, [trackers, activeTab, commentFilter, tagFilter])

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
    // Convert uppercase CommentType to lowercase for API (backend expects 'programming' or 'biostat')
    const apiCommentType = newComment.type.toLowerCase() as 'programming' | 'biostat'
    createComment.mutate({
      tracker_id: selectedTracker.id,
      comment_text: newComment.text.trim(),
      comment_type: apiCommentType,
      parent_comment_id: newComment.parentId,
    })
  }

  const handleReply = (comment: TrackerComment) => {
    setReplyingTo(comment)
    // Keep the current comment type (programming/biostat) for replies
    setNewComment(prev => ({ ...prev, parentId: comment.id }))
  }

  const cancelReply = () => {
    setReplyingTo(null)
    setNewComment(prev => ({ ...prev, parentId: null }))
  }

  const handleDelete = (tracker: ReportingEffortItemTracker) => {
    setSelectedTracker(tracker)
    setDeleteDialogOpen(true)
  }

  const handleCreateTag = () => {
    if (!newTag.name.trim()) return
    createTag.mutate(newTag)
  }

  const handleUpdateTag = () => {
    if (!editingTag) return
    updateTag.mutate({
      id: editingTag.id,
      data: { name: editingTag.name, color: editingTag.color, description: editingTag.description }
    })
  }

  // All users can be assigned as programmers
  const programmers = users

  const getProgrammerName = (id?: number) => {
    if (!id) return '-'
    const user = users.find((u) => u.id === id)
    return user?.username || '-'
  }

  // Get comment type label
  const getCommentTypeLabel = (type: CommentType) => {
    const found = COMMENT_TYPES.find(t => t.value === type)
    return found?.label || type
  }

  // Define table columns - changes based on active tab
  const getColumns = (): ColumnDef<ReportingEffortItemTracker>[] => {
    const baseColumns: ColumnDef<ReportingEffortItemTracker>[] = [
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
        helpText: 'Unique identifier for the reporting item.',
        cell: (value) => <span className="font-medium">{value}</span>,
      },
    ]

    // For TLF tab, show Title; for others, just show item code
    if (activeTab === 'tlf') {
      baseColumns.push({
        id: 'item_title',
        header: 'Title',
        accessorKey: 'item_title',
        filterType: 'text',
        helpText: 'Title of the TLF output.',
        cell: (value) => <span className="max-w-xs truncate block">{value || '-'}</span>,
      })
    }

    // Tags column
    baseColumns.push({
      id: 'tags',
      header: 'Tags',
      accessorKey: 'tags',
      filterType: 'none',
      enableSorting: false,
      cell: (_, tracker) => (
        <div className="flex flex-wrap gap-1 items-center">
          {tracker.tags?.map((tag) => (
            <Badge
              key={tag.id}
              style={{ backgroundColor: tag.color, color: getContrastColor(tag.color) }}
              className="text-xs cursor-pointer hover:opacity-80"
              onClick={() => removeTag.mutate({ trackerId: tracker.id, tagId: tag.id })}
            >
              {tag.name}
              <X className="h-3 w-3 ml-1" />
            </Badge>
          ))}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                <Plus className="h-3 w-3" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-48 p-2">
              <div className="space-y-1">
                {allTags.filter(t => !tracker.tags?.some(tt => tt.id === t.id)).map((tag) => (
                  <Button
                    key={tag.id}
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start"
                    onClick={() => assignTag.mutate({ trackerId: tracker.id, tagId: tag.id })}
                  >
                    <div
                      className="w-3 h-3 rounded-full mr-2"
                      style={{ backgroundColor: tag.color }}
                    />
                    {tag.name}
                  </Button>
                ))}
                {allTags.length === 0 && (
                  <p className="text-xs text-muted-foreground p-2">No tags available</p>
                )}
              </div>
            </PopoverContent>
          </Popover>
        </div>
      ),
    })

    // Rest of columns
    baseColumns.push(
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
        id: 'comments',
        header: 'Comments',
        accessorKey: 'unresolved_comment_count',
        filterType: 'none',
        enableSorting: true,
        cell: (_, tracker) => (
          <TooltipWrapper 
            content={`${tracker.comment_count || 0} total, ${tracker.unresolved_comment_count || 0} unresolved`}
          >
            <Button variant="ghost" size="sm" onClick={() => handleOpenComments(tracker)}>
              <MessageSquare className="h-4 w-4" />
              {(tracker.unresolved_comment_count || 0) > 0 ? (
                <Badge variant="destructive" className="ml-1">{tracker.unresolved_comment_count}</Badge>
              ) : tracker.comment_count ? (
                <Badge variant="secondary" className="ml-1">{tracker.comment_count}</Badge>
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
            <TooltipWrapper content="Edit tracker">
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
      }
    )

    return baseColumns
  }

  const columns = useMemo(() => getColumns(), [activeTab, selectedRows, users, allTags])

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
                Manage programmer assignments, status tracking, and tags
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
                      <li>Tag items (e.g., Topline, Batch 1)</li>
                      <li>Comment threads for communication</li>
                      <li>Bulk operations for efficiency</li>
                    </ul>
                  </div>
                </div>
              }
            />
          </div>
          <div className="flex gap-2">
            <TooltipWrapper content="Manage tags">
              <Button variant="outline" size="sm" onClick={() => setTagManageOpen(true)}>
                <Tag className="h-4 w-4 mr-2" />
                Manage Tags
              </Button>
            </TooltipWrapper>
            <TooltipWrapper content="Refresh tracker data">
              <Button variant="outline" size="sm" onClick={refetch} disabled={!selectedEffortId}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </TooltipWrapper>
            {selectedRows.size > 0 && (
              <>
                <TooltipWrapper content={`Assign tag to ${selectedRows.size} selected trackers`}>
                  <Button variant="outline" size="sm" onClick={() => setBulkTagOpen(true)}>
                    <Tag className="h-4 w-4 mr-2" />
                    Tag ({selectedRows.size})
                  </Button>
                </TooltipWrapper>
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
          <div className="flex gap-4 mb-4 flex-wrap">
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
            
            {/* Filters */}
            {selectedEffortId && (
              <>
                <div className="w-48">
                  <Label>Comment Filter</Label>
                  <Select value={commentFilter} onValueChange={(v: 'all' | 'has_comments' | 'has_unresolved') => setCommentFilter(v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Items</SelectItem>
                      <SelectItem value="has_comments">Has Comments</SelectItem>
                      <SelectItem value="has_unresolved">Unresolved Comments</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="w-48">
                  <Label>Tag Filter</Label>
                  <Select value={tagFilter?.toString() || 'all'} onValueChange={(v) => setTagFilter(v === 'all' ? null : Number(v))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Tags</SelectItem>
                      {allTags.map((tag) => (
                        <SelectItem key={tag.id} value={String(tag.id)}>
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: tag.color }} />
                            {tag.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
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
                      description={commentFilter !== 'all' || tagFilter !== null ? "No items match the current filters." : "No items in this tracker."}
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
      <Dialog open={commentDialogOpen} onOpenChange={(open) => { setCommentDialogOpen(open); if (!open) { setReplyingTo(null); setNewComment({ text: '', type: 'PROGRAMMING', parentId: null }) } }}>
        <DialogContent className="max-w-2xl max-h-[85vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Comments for {selectedTracker?.item_code}
            </DialogTitle>
            <DialogDescription>
              Communicate with programmers and QC team
            </DialogDescription>
          </DialogHeader>
          
          {/* Comment List */}
          <ScrollArea className="h-[350px] pr-4">
            {comments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No comments yet. Start the conversation below.
              </div>
            ) : (
              <div className="space-y-4">
                {comments.map((comment) => (
                  <CommentItem 
                    key={comment.id} 
                    comment={comment} 
                    onResolve={() => resolveComment.mutate(comment.id)}
                    onReply={handleReply}
                    getCommentTypeLabel={getCommentTypeLabel}
                    isNested={false}
                  />
                ))}
              </div>
            )}
          </ScrollArea>

          {/* Add Comment Form */}
          <div className="border-t pt-4 mt-4">
            {replyingTo && (
              <div className="flex items-center gap-2 mb-2 p-2 bg-muted rounded text-sm">
                <Reply className="h-4 w-4" />
                <span>Replying to {replyingTo.user?.username || 'Unknown'}</span>
                <Button variant="ghost" size="sm" className="ml-auto h-6" onClick={cancelReply}>
                  <X className="h-3 w-3" />
                </Button>
              </div>
            )}
            <div className="flex gap-2 mb-2">
              <Select
                value={newComment.type}
                onValueChange={(v: CommentType) => setNewComment((prev) => ({ ...prev, type: v }))}
              >
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {COMMENT_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2">
              <Textarea
                placeholder={replyingTo ? "Write your reply..." : "Add a comment..."}
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

      {/* Tag Management Dialog */}
      <Dialog open={tagManageOpen} onOpenChange={setTagManageOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5" />
              Manage Tags
            </DialogTitle>
            <DialogDescription>
              Create, edit, or delete tags for categorizing tracker items
            </DialogDescription>
          </DialogHeader>
          
          {/* Create new tag */}
          <div className="space-y-3 p-3 border rounded-lg bg-muted/30">
            <Label className="font-medium">Create New Tag</Label>
            <div className="flex gap-2">
              <Input
                placeholder="Tag name (e.g., Topline)"
                value={newTag.name}
                onChange={(e) => setNewTag(prev => ({ ...prev, name: e.target.value }))}
                className="flex-1"
              />
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-24" style={{ backgroundColor: newTag.color }}>
                    <span style={{ color: getContrastColor(newTag.color) }}>Color</span>
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-64">
                  <div className="grid grid-cols-6 gap-2">
                    {TAG_COLORS.map((color) => (
                      <button
                        key={color}
                        className={`w-8 h-8 rounded-full border-2 ${newTag.color === color ? 'border-foreground' : 'border-transparent'}`}
                        style={{ backgroundColor: color }}
                        onClick={() => setNewTag(prev => ({ ...prev, color }))}
                      />
                    ))}
                  </div>
                </PopoverContent>
              </Popover>
              <Button onClick={handleCreateTag} disabled={!newTag.name.trim()}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Existing tags */}
          <ScrollArea className="h-[250px]">
            <div className="space-y-2">
              {allTags.map((tag) => (
                <div key={tag.id} className="flex items-center gap-2 p-2 border rounded hover:bg-muted/50">
                  {editingTag?.id === tag.id ? (
                    <>
                      <Input
                        value={editingTag.name}
                        onChange={(e) => setEditingTag(prev => prev ? { ...prev, name: e.target.value } : null)}
                        className="flex-1 h-8"
                      />
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button variant="outline" size="sm" style={{ backgroundColor: editingTag.color }}>
                            <span style={{ color: getContrastColor(editingTag.color) }}>Color</span>
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-64">
                          <div className="grid grid-cols-6 gap-2">
                            {TAG_COLORS.map((color) => (
                              <button
                                key={color}
                                className={`w-8 h-8 rounded-full border-2 ${editingTag.color === color ? 'border-foreground' : 'border-transparent'}`}
                                style={{ backgroundColor: color }}
                                onClick={() => setEditingTag(prev => prev ? { ...prev, color } : null)}
                              />
                            ))}
                          </div>
                        </PopoverContent>
                      </Popover>
                      <Button size="sm" onClick={handleUpdateTag}>Save</Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingTag(null)}>Cancel</Button>
                    </>
                  ) : (
                    <>
                      <Badge style={{ backgroundColor: tag.color, color: getContrastColor(tag.color) }}>
                        {tag.name}
                      </Badge>
                      <span className="text-xs text-muted-foreground ml-auto">
                        {tag.usage_count || 0} uses
                      </span>
                      <Button size="sm" variant="ghost" onClick={() => setEditingTag(tag)}>
                        <Edit className="h-3 w-3" />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => deleteTag.mutate(tag.id)}>
                        <Trash2 className="h-3 w-3 text-destructive" />
                      </Button>
                    </>
                  )}
                </div>
              ))}
              {allTags.length === 0 && (
                <p className="text-center py-4 text-muted-foreground">No tags created yet</p>
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Bulk Tag Assignment Dialog */}
      <Dialog open={bulkTagOpen} onOpenChange={setBulkTagOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bulk Assign Tag</DialogTitle>
            <DialogDescription>
              Assign a tag to {selectedRows.size} selected tracker(s).
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Select Tag</Label>
              <Select onValueChange={(v) => {
                bulkAssignTag.mutate({ tracker_ids: Array.from(selectedRows), tag_id: Number(v) })
              }}>
                <SelectTrigger><SelectValue placeholder="Choose a tag" /></SelectTrigger>
                <SelectContent>
                  {allTags.map((tag) => (
                    <SelectItem key={tag.id} value={String(tag.id)}>
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: tag.color }} />
                        {tag.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkTagOpen(false)}>Cancel</Button>
          </DialogFooter>
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

// Helper function to get contrasting text color
function getContrastColor(hexColor: string): string {
  const r = parseInt(hexColor.slice(1, 3), 16)
  const g = parseInt(hexColor.slice(3, 5), 16)
  const b = parseInt(hexColor.slice(5, 7), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.5 ? '#000000' : '#FFFFFF'
}

// Comment Item Component with reply functionality
function CommentItem({ 
  comment, 
  onResolve, 
  onReply,
  getCommentTypeLabel,
  isNested = false
}: { 
  comment: TrackerComment
  onResolve: () => void
  onReply: (comment: TrackerComment) => void
  getCommentTypeLabel: (type: CommentType) => string
  isNested?: boolean
}) {
  const typeColors: Record<string, string> = {
    'PROGRAMMING': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    'BIOSTAT': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    'QUESTION': 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
    'ISSUE': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    'RESPONSE': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  }

  return (
    <div className={`p-3 rounded-lg border ${comment.is_resolved ? 'bg-muted/50 opacity-70' : 'bg-card'} ${isNested ? 'ml-6 mt-2' : ''}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="font-semibold text-sm">{comment.user?.username || 'Unknown'}</span>
            <Badge variant="outline" className={`text-xs ${typeColors[comment.comment_type] || ''}`}>
              {getCommentTypeLabel(comment.comment_type)}
            </Badge>
            {comment.is_resolved && <Badge variant="secondary" className="text-xs">Resolved</Badge>}
            <span className="text-xs text-muted-foreground">{formatDateTime(comment.created_at)}</span>
          </div>
          <p className="text-sm whitespace-pre-wrap">{comment.comment_text}</p>
        </div>
        <div className="flex gap-1">
          {!isNested && !comment.is_resolved && (
            <Button variant="ghost" size="sm" onClick={() => onReply(comment)}>
              <Reply className="h-4 w-4" />
            </Button>
          )}
          {!isNested && !comment.is_resolved && (
            <Button variant="ghost" size="sm" onClick={onResolve}>
              <CheckCircle className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
      {/* Nested Replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="border-l-2 border-muted ml-2 mt-2">
          {comment.replies.map((reply) => (
            <CommentItem 
              key={reply.id} 
              comment={reply} 
              onResolve={() => {}}
              onReply={() => {}}
              getCommentTypeLabel={getCommentTypeLabel}
              isNested={true}
            />
          ))}
        </div>
      )}
    </div>
  )
}
