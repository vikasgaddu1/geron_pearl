import { useState, useCallback, useMemo, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ClipboardCheck, RefreshCw, Users, CheckCircle, MessageSquare, Edit, Trash2, Send, X, Tag, Plus, Reply, LayoutList, Kanban, UserCheck, Calendar, Factory, AlertTriangle, Target, CheckSquare } from 'lucide-react'
import { toast } from 'sonner'
import { reportingEffortsApi, trackerApi, trackerCommentsApi, trackerTagsApi, usersApi, studiesApi, databaseReleasesApi, useDefaultDueDateOffset, phasesApi, milestonesApi } from '@/api'
import { useReportingSelectionStore } from '@/stores/reportingSelectionStore'
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
import type { ReportingEffortItemTracker, TrackerStatus, TrackerComment, CommentType, Priority, TrackerTag, ProductionStatus, QCStatus } from '@/types'
import { KanbanBoard, QCFailureCommentDialog } from '@/components/tracker'
import { useAuthStore } from '@/stores/authStore'
import { MilestoneEditor } from './MilestoneEditor'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'

// Separate status arrays for Production and QC
const PRODUCTION_STATUSES: ProductionStatus[] = ['not_started', 'in_progress', 'ready_for_qc', 'on_hold']
// Note: 'completed' is excluded because it's auto-set by QC completion
const QC_STATUSES: QCStatus[] = ['not_started', 'in_progress', 'on_hold']
// Note: 'failed' and 'completed' are only allowed when production is ready_for_qc
const QC_STATUSES_READY: QCStatus[] = ['not_started', 'in_progress', 'failed', 'completed', 'on_hold']
// Legacy combined list for backward compatibility
const TRACKER_STATUSES: TrackerStatus[] = ['not_started', 'in_progress', 'ready_for_qc', 'completed', 'on_hold', 'failed']
const PRIORITIES: Priority[] = ['critical', 'high', 'medium', 'low']

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
  const [searchParams, setSearchParams] = useSearchParams()
  const { currentUser } = useAuthStore()
  // Use persisted store for selection state (shared with ReportingEffortItems)
  const { 
    selectedStudyId, 
    selectedReleaseId, 
    selectedEffortId,
    setSelectedStudyId,
    setSelectedReleaseId,
    setSelectedEffortId 
  } = useReportingSelectionStore()
  const [urlParamsApplied, setUrlParamsApplied] = useState(false)
  const [activeTab, setActiveTab] = useState('tlf')
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())
  const [bulkAssignStatusOpen, setBulkAssignStatusOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [commentDialogOpen, setCommentDialogOpen] = useState(false)
  const [commentDialogContext, setCommentDialogContext] = useState<'list' | 'production' | 'qc'>('list') // Track where dialog was opened from
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [tagManageOpen, setTagManageOpen] = useState(false)
  const [bulkTagOpen, setBulkTagOpen] = useState(false)
  const [bulkMilestoneOpen, setBulkMilestoneOpen] = useState(false)
  const [bulkMilestoneId, setBulkMilestoneId] = useState<number | null>(null)
  const [selectedTracker, setSelectedTracker] = useState<ReportingEffortItemTracker | null>(null)
  
  // QC Failure comment dialog state
  const [qcFailureDialogOpen, setQcFailureDialogOpen] = useState(false)
  const [qcFailureTrackerId, setQcFailureTrackerId] = useState<number | null>(null)
  const [qcFailureTrackerCode, setQcFailureTrackerCode] = useState<string | undefined>(undefined)

  // Get default due date offset from settings
  const { data: dueDateOffset = 7 } = useDefaultDueDateOffset()

  // Helper to get default due date (today + configurable offset)
  const getDefaultDueDate = useCallback(() => {
    const d = new Date()
    d.setDate(d.getDate() + dueDateOffset)
    return d.toISOString().split('T')[0]
  }, [dueDateOffset])
  
  const [bulkData, setBulkData] = useState({
    production_programmer_id: '',
    qc_programmer_id: '',
    production_status: '' as ProductionStatus | '',
    qc_status: '' as QCStatus | '',
    due_date: '',
    priority: '' as Priority | '',
  })
  const [editFormData, setEditFormData] = useState({
    production_programmer_id: '',
    qc_programmer_id: '',
    production_status: 'not_started' as ProductionStatus,
    qc_status: 'not_started' as QCStatus,
    priority: 'medium' as Priority,
    due_date: '',
    milestone_ids: [] as number[],
  })
  const [newComment, setNewComment] = useState({ 
    text: '', 
    type: 'PROGRAMMING' as CommentType, 
    parentId: null as number | null,
    // New: status updates in comment dialog
    production_status: undefined as ProductionStatus | undefined,
    qc_status: undefined as QCStatus | undefined,
  })
  const [replyingTo, setReplyingTo] = useState<TrackerComment | null>(null)
  
  // Filter states
  const [commentFilter, setCommentFilter] = useState<'all' | 'has_comments' | 'has_unresolved'>('all')
  const [tagFilter, setTagFilter] = useState<number | null>(null)
  const [milestoneFilter, setMilestoneFilter] = useState<number | null>(null)
  const [itemCodeFilter, setItemCodeFilter] = useState<string | null>(null)
  
  // View and filter mode states
  const [viewMode, setViewMode] = useState<'list' | 'kanban-prod' | 'kanban-qc'>('list')
  const [taskFilter, setTaskFilter] = useState<'all' | 'my-tasks'>('all')
  
  // Tag management state
  const [newTag, setNewTag] = useState({ name: '', color: '#3B82F6', description: '' })
  const [editingTag, setEditingTag] = useState<TrackerTag | null>(null)

  // Queries
  const { data: studies = [] } = useQuery({
    queryKey: ['studies'],
    queryFn: studiesApi.getAll,
  })

  const { data: allReleases = [] } = useQuery({
    queryKey: ['database-releases'],
    queryFn: databaseReleasesApi.getAll,
  })

  const { data: efforts = [], isLoading: effortsLoading } = useQuery({
    queryKey: ['reporting-efforts'],
    queryFn: reportingEffortsApi.getAll,
  })

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.getAll,
  })

  // Filtered data based on cascaded selections
  const filteredReleases = useMemo(() => {
    if (!selectedStudyId) return []
    return allReleases.filter(r => r.study_id === Number(selectedStudyId))
  }, [allReleases, selectedStudyId])

  const filteredEfforts = useMemo(() => {
    if (!selectedReleaseId) return []
    return efforts.filter(e => e.database_release_id === Number(selectedReleaseId))
  }, [efforts, selectedReleaseId])

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

  // Study-scoped permissions for bulk operations
  const { data: studyPermissions } = useQuery({
    queryKey: ['study-permissions', selectedStudyId],
    queryFn: () => studiesApi.getMyPermissions(Number(selectedStudyId)),
    enabled: !!selectedStudyId,
  })

  // Query phases/milestones for the current reporting effort (for milestone dropdown in edit dialog)
  const { data: phases = [] } = useQuery({
    queryKey: ['phases', selectedEffortId],
    queryFn: () => (selectedEffortId ? phasesApi.getByReportingEffort(Number(selectedEffortId)) : Promise.resolve([])),
    enabled: !!selectedEffortId,
  })

  // Flatten milestones from phases for easy access
  const availableMilestones = useMemo(() => {
    return phases.flatMap(phase =>
      (phase.milestones || []).map(m => ({
        ...m,
        phase_name: phase.name,
      }))
    )
  }, [phases])

  // Query tracker's manual milestone assignments when edit dialog is open
  const { data: trackerMilestoneIds = [] } = useQuery({
    queryKey: ['tracker-milestones', selectedTracker?.id],
    queryFn: () => (selectedTracker ? trackerApi.getMilestones(selectedTracker.id) : Promise.resolve([])),
    enabled: !!selectedTracker && editDialogOpen,
  })

  // Check if current user can perform bulk operations
  const canBulkAssign = currentUser?.is_admin || studyPermissions?.can_bulk_assign === true
  const canBulkStatusUpdate = currentUser?.is_admin || studyPermissions?.can_bulk_status_update === true
  const canDeleteTrackers = currentUser?.is_admin || studyPermissions?.can_delete_items === true
  
  // Check if current user is a Study LEAD (for individual tracker operations)
  const isStudyLead = studyPermissions?.role === 'LEAD'

  // WebSocket refresh
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
    queryClient.invalidateQueries({ queryKey: ['tracker-tags'] })
  }, [queryClient, selectedEffortId])

  useWebSocketRefresh(['reporting_effort_tracker', 'reporting_effort_item', 'comment', 'tracker_tag'], refetch)

  // Handle URL query parameters for deep linking from dashboard
  useEffect(() => {
    if (urlParamsApplied) return
    
    const studyIdParam = searchParams.get('studyId')
    const effortIdParam = searchParams.get('effortId')
    const itemCodeParam = searchParams.get('itemCode')
    const itemSubtypeParam = searchParams.get('itemSubtype')
    
    if (!studyIdParam || studies.length === 0 || efforts.length === 0 || allReleases.length === 0) {
      return
    }
    
    // Find the effort to get the release ID
    const effort = efforts.find(e => e.id === Number(effortIdParam))
    if (!effort) return
    
    // Set the study
    setSelectedStudyId(studyIdParam)
    
    // Set the release
    setSelectedReleaseId(String(effort.database_release_id))
    
    // Set the effort (with a small delay to let the cascade work)
    setTimeout(() => {
      setSelectedEffortId(effortIdParam || '')
      // Apply item code filter if provided (for deep linking to specific item)
      if (itemCodeParam) {
        setItemCodeFilter(itemCodeParam)
      }
      // Auto-select the correct tab based on item subtype
      if (itemSubtypeParam) {
        const subtype = itemSubtypeParam.toLowerCase()
        if (['table', 'listing', 'figure'].includes(subtype)) {
          setActiveTab('tlf')
        } else if (subtype === 'sdtm') {
          setActiveTab('sdtm')
        } else if (subtype === 'adam') {
          setActiveTab('adam')
        }
      }
      // Clear the URL params after applying
      setSearchParams({}, { replace: true })
      setUrlParamsApplied(true)
    }, 100)
  }, [searchParams, studies, efforts, allReleases, urlParamsApplied, setSearchParams])

  // Mutations
  const bulkAssignStatus = useMutation({
    mutationFn: trackerApi.bulkAssignStatus,
    onSuccess: (result) => {
      if (result.failed > 0) {
        toast.warning(`Updated ${result.updated} trackers, ${result.failed} failed`, {
          description: result.errors.slice(0, 3).join('\n'),
          duration: 8000,
        })
      } else {
        toast.success(`Updated ${result.updated} trackers`)
      }
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      setBulkAssignStatusOpen(false)
      setSelectedRows(new Set())
      // Reset form
      setBulkData({
        production_programmer_id: '',
        qc_programmer_id: '',
        production_status: '',
        qc_status: '',
        due_date: '',
        priority: '',
      })
    },
    onError: (error) => toast.error(`Failed to update: ${getErrorMessage(error)}`),
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

  const updateProductionFlag = useMutation({
    mutationFn: ({ trackerId, value }: { trackerId: number; value: boolean }) =>
      trackerApi.updateProductionFlag(trackerId, value),
    onSuccess: () => {
      toast.success('Production flag updated')
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
    },
    onError: (error) => toast.error(`Failed to update production flag: ${getErrorMessage(error)}`),
  })

  const updateTrackerMilestones = useMutation({
    mutationFn: ({ trackerId, milestoneIds }: { trackerId: number; milestoneIds: number[] }) =>
      trackerApi.updateMilestones(trackerId, milestoneIds),
    onSuccess: (result) => {
      if (result.added > 0 || result.removed > 0) {
        toast.success(`Milestones updated: ${result.added} added, ${result.removed} removed`)
      }
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      queryClient.invalidateQueries({ queryKey: ['tracker-milestones', selectedTracker?.id] })
    },
    onError: (error) => toast.error(`Failed to update milestones: ${getErrorMessage(error)}`),
  })

  // Bulk assign trackers to a milestone
  const bulkAssignMilestone = useMutation({
    mutationFn: ({ milestoneId, trackerIds }: { milestoneId: number; trackerIds: number[] }) =>
      milestonesApi.linkTrackers(milestoneId, trackerIds),
    onSuccess: (result) => {
      if (result.affected_count > 0) {
        toast.success(`Assigned ${result.affected_count} trackers to milestone`)
      } else {
        toast.info('No new assignments - trackers were already linked to this milestone')
      }
      queryClient.invalidateQueries({ queryKey: ['trackers', selectedEffortId] })
      queryClient.invalidateQueries({ queryKey: ['phases', selectedEffortId] })
      setBulkMilestoneOpen(false)
      setBulkMilestoneId(null)
      setSelectedRows(new Set())
    },
    onError: (error) => toast.error(`Failed to assign milestone: ${getErrorMessage(error)}`),
  })

  const createComment = useMutation({
    mutationFn: trackerCommentsApi.create,
    onSuccess: () => {
      toast.success('Comment added')
      refetchComments()
      setNewComment({ text: '', type: 'PROGRAMMING', parentId: null, production_status: undefined, qc_status: undefined })
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
    
    // My Tasks filter
    if (taskFilter === 'my-tasks' && currentUser) {
      result = result.filter(t => 
        t.production_programmer_id === currentUser.id || 
        t.qc_programmer_id === currentUser.id
      )
    }
    
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

    // Milestone filter
    if (milestoneFilter !== null) {
      result = result.filter(t => t.milestones?.some(m => m.milestone_id === milestoneFilter))
    }

    // Item code filter (for deep linking to specific item)
    if (itemCodeFilter) {
      result = result.filter(t => t.item_code === itemCodeFilter)
    }

    return result
  }, [trackers, activeTab, commentFilter, tagFilter, milestoneFilter, taskFilter, currentUser, itemCodeFilter])

  const handleSelectRow = (id: number, checked: boolean) => {
    const newSelected = new Set(selectedRows)
    if (checked) {
      newSelected.add(id)
    } else {
      newSelected.delete(id)
    }
    setSelectedRows(newSelected)
  }

  const handleBulkAssignStatus = () => {
    const data: Parameters<typeof trackerApi.bulkAssignStatus>[0] = {
      tracker_ids: Array.from(selectedRows),
    }
    
    // Only include fields that are set
    if (bulkData.production_programmer_id) {
      data.production_programmer_id = Number(bulkData.production_programmer_id)
      // Include due_date if set (will be auto-set on backend if not provided)
      if (bulkData.due_date) {
        data.due_date = bulkData.due_date
      }
    }
    if (bulkData.qc_programmer_id) {
      data.qc_programmer_id = Number(bulkData.qc_programmer_id)
    }
    if (bulkData.production_status) {
      data.production_status = bulkData.production_status as ProductionStatus
    }
    if (bulkData.qc_status) {
      data.qc_status = bulkData.qc_status as QCStatus
    }
    if (bulkData.priority) {
      data.priority = bulkData.priority as Priority
    }
    
    bulkAssignStatus.mutate(data)
  }
  
  // Check if bulk form has any changes
  const hasBulkChanges = useMemo(() => {
    return !!(
      bulkData.production_programmer_id ||
      bulkData.qc_programmer_id ||
      bulkData.production_status ||
      bulkData.qc_status ||
      bulkData.due_date ||
      bulkData.priority
    )
  }, [bulkData])

  const handleEdit = (tracker: ReportingEffortItemTracker) => {
    setSelectedTracker(tracker)
    setEditFormData({
      production_programmer_id: tracker.production_programmer_id?.toString() || '',
      qc_programmer_id: tracker.qc_programmer_id?.toString() || '',
      production_status: tracker.production_status || 'not_started',
      qc_status: tracker.qc_status || 'not_started',
      priority: (tracker.priority as Priority) || 'medium',
      due_date: tracker.due_date || '',
      milestone_ids: [], // Will be populated by the query effect below
    })
    setEditDialogOpen(true)
  }

  // Populate milestone_ids when the query loads
  useEffect(() => {
    if (editDialogOpen && trackerMilestoneIds.length >= 0) {
      setEditFormData(prev => ({
        ...prev,
        milestone_ids: trackerMilestoneIds,
      }))
    }
  }, [editDialogOpen, trackerMilestoneIds])

  const handleEditSubmit = () => {
    if (!selectedTracker) return
    
    // Validate: Cannot change production status without production programmer
    const newProdProgrammer = editFormData.production_programmer_id || selectedTracker.production_programmer_id
    if (editFormData.production_status && editFormData.production_status !== 'not_started' && !newProdProgrammer) {
      toast.error('Cannot update production status without a production programmer assigned')
      return
    }
    
    // Validate: Production status cannot be set to 'completed' directly - it's auto-set by QC completion
    if (editFormData.production_status === 'completed' && selectedTracker.production_status !== 'completed') {
      toast.error("Production status cannot be set to 'Completed' directly. It is automatically set when QC marks the item as completed.")
      return
    }
    
    // Validate: Cannot change QC status without QC programmer
    const newQcProgrammer = editFormData.qc_programmer_id || selectedTracker.qc_programmer_id
    if (editFormData.qc_status && editFormData.qc_status !== 'not_started' && !newQcProgrammer) {
      toast.error('Cannot update QC status without a QC programmer assigned')
      return
    }
    
    // Validate: QC 'completed' or 'failed' only allowed when production is 'ready_for_qc'
    if ((editFormData.qc_status === 'completed' || editFormData.qc_status === 'failed') && 
        editFormData.production_status !== 'ready_for_qc' && selectedTracker.production_status !== 'ready_for_qc') {
      toast.error(`QC can only be marked as '${editFormData.qc_status === 'completed' ? 'Completed' : 'Failed'}' when production status is 'Ready for QC'`)
      return
    }
    
    // Validate: Due date is required when production programmer is assigned
    if (newProdProgrammer && !editFormData.due_date && !selectedTracker.due_date) {
      toast.error('Due date is required when a production programmer is assigned')
      return
    }
    
    // Validate: Cannot mark QC as completed if there are unresolved comments
    if (editFormData.qc_status === 'completed' && (selectedTracker.unresolved_comment_count || 0) > 0) {
      toast.error(`Cannot mark QC as completed: ${selectedTracker.unresolved_comment_count} unresolved comment(s) must be addressed first`)
      return
    }
    
    // Intercept QC status change to 'failed' - require comment
    if (editFormData.qc_status === 'failed' && selectedTracker.qc_status !== 'failed') {
      setEditDialogOpen(false)
      setQcFailureTrackerId(selectedTracker.id)
      setQcFailureTrackerCode(selectedTracker.item_code)
      setQcFailureDialogOpen(true)
      return
    }
    
    // Build update data based on user permissions - only send what they can change
    const isAdmin = currentUser?.is_admin
    const isProductionProgrammer = currentUser && selectedTracker.production_programmer_id === currentUser.id
    const isQCProgrammer = currentUser && selectedTracker.qc_programmer_id === currentUser.id
    // Study LEAD has full edit access like admin
    const canEditProduction = isAdmin || isStudyLead || isProductionProgrammer
    const canEditQC = isAdmin || isStudyLead || isQCProgrammer
    
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const updateData: any = {}
    
    // Admin or Study LEAD can change everything
    if (isAdmin || isStudyLead) {
      updateData.production_programmer_id = editFormData.production_programmer_id ? Number(editFormData.production_programmer_id) : null
      updateData.qc_programmer_id = editFormData.qc_programmer_id ? Number(editFormData.qc_programmer_id) : null
      updateData.production_status = editFormData.production_status
      updateData.qc_status = editFormData.qc_status
      updateData.priority = editFormData.priority
      updateData.due_date = editFormData.due_date || null
    } else {
      // Non-admin/non-lead: only send fields they have permission to change
      if (canEditProduction) {
        updateData.production_status = editFormData.production_status
        updateData.priority = editFormData.priority
        updateData.due_date = editFormData.due_date || null
      }
      if (canEditQC) {
        updateData.qc_status = editFormData.qc_status
      }
    }

    // Update tracker
    updateTracker.mutate({
      id: selectedTracker.id,
      data: updateData,
    })

    // Update milestones if changed (admin, study lead, or production programmer can update)
    if (isAdmin || isStudyLead || canEditProduction) {
      const currentMilestoneIds = new Set(trackerMilestoneIds)
      const newMilestoneIds = new Set(editFormData.milestone_ids)

      // Check if milestones have changed
      const milestonesChanged =
        currentMilestoneIds.size !== newMilestoneIds.size ||
        [...currentMilestoneIds].some(id => !newMilestoneIds.has(id))

      if (milestonesChanged) {
        updateTrackerMilestones.mutate({
          trackerId: selectedTracker.id,
          milestoneIds: editFormData.milestone_ids,
        })
      }
    }
  }

  const handleOpenComments = (tracker: ReportingEffortItemTracker) => {
    setSelectedTracker(tracker)
    setCommentDialogContext('list') // From list view, show both status options
    setCommentDialogOpen(true)
  }

  const handleProductionFlagToggle = (trackerId: number, newValue: boolean) => {
    const tracker = trackers.find(t => t.id === trackerId)
    if (!tracker) return
    
    // Validate: can only set to true if both statuses are completed
    if (newValue && (tracker.production_status !== 'completed' || tracker.qc_status !== 'completed')) {
      toast.error('Both Production and QC must be Completed to set In Production flag')
      return
    }
    
    updateProductionFlag.mutate({ trackerId, value: newValue })
  }

  const handleAddComment = async () => {
    if (!selectedTracker || !newComment.text.trim()) return
    
    // Validate: Production status cannot be set to 'completed' directly
    if (newComment.production_status === 'completed') {
      toast.error("Production status cannot be set to 'Completed' directly. It is automatically set when QC marks the item as completed.")
      return
    }
    
    // Validate: QC 'completed' or 'failed' only allowed when production is 'ready_for_qc'
    if ((newComment.qc_status === 'completed' || newComment.qc_status === 'failed') && selectedTracker.production_status !== 'ready_for_qc') {
      toast.error(`QC can only be marked as '${newComment.qc_status === 'completed' ? 'Completed' : 'Failed'}' when production status is 'Ready for QC'`)
      return
    }
    
    // Validate: Cannot mark QC as completed if there are unresolved comments
    if (newComment.qc_status === 'completed' && (selectedTracker.unresolved_comment_count || 0) > 0) {
      toast.error(`Cannot mark QC as completed: ${selectedTracker.unresolved_comment_count} unresolved comment(s) must be addressed first`)
      return
    }
    
    // If status updates are included and it's a top-level comment, use the new endpoint
    if ((newComment.production_status || newComment.qc_status) && !newComment.parentId) {
      try {
        const result = await trackerApi.createCommentWithStatus(selectedTracker.id, {
          comment_text: newComment.text.trim(),
          production_status: newComment.production_status,
          qc_status: newComment.qc_status,
        })
        
        toast.success('Comment added and status updated')
        queryClient.invalidateQueries({ queryKey: ['trackerComments', selectedTracker.id] })
        queryClient.invalidateQueries({ queryKey: ['trackers'] })
        setNewComment({ text: '', type: 'PROGRAMMING', parentId: null, production_status: undefined, qc_status: undefined })
        
        // Update selected tracker with new data
        if (result.tracker) {
          setSelectedTracker(result.tracker)
        }
      } catch (error) {
        toast.error(getErrorMessage(error))
      }
    } else {
      // Regular comment without status update
      // Convert uppercase CommentType to lowercase for API (backend expects 'programming' or 'biostat')
      const apiCommentType = newComment.type.toLowerCase() as 'programming' | 'biostat'
      createComment.mutate({
        tracker_id: selectedTracker.id,
        comment_text: newComment.text.trim(),
        comment_type: apiCommentType,
        parent_comment_id: newComment.parentId,
      })
    }
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

  // All users can be assigned as programmers - their access is determined by study roles
  const programmers = useMemo(() => users, [users])

  const getProgrammerName = (id?: number) => {
    if (!id) return '-'
    const user = users.find((u) => u.id === id)
    return user?.username || '-'
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
        cell: (value, tracker) => {
          const milestones = tracker.milestones || []
          const hasMilestones = milestones.length > 0
          const isCompleted = tracker.qc_status === 'completed'
          // Only show red if there are past-due milestones AND item is not completed
          const hasPastDue = !isCompleted && milestones.some(m => m.is_past_due)

          return (
            <div className="flex items-center gap-1.5">
              <span className="font-medium">{value}</span>
              {hasMilestones && (
                <TooltipWrapper
                  content={
                    <div className="text-xs space-y-1">
                      <div className="font-medium mb-1">Linked Milestones:</div>
                      {milestones.map((m) => (
                        <div key={m.milestone_id} className="flex items-center gap-2">
                          <Target className="h-3 w-3" />
                          <span>{m.milestone_name}</span>
                          {m.milestone_due_date && (
                            <span className={m.is_past_due && !isCompleted ? 'text-red-400' : 'text-muted-foreground'}>
                              (Due: {formatDate(m.milestone_due_date)})
                            </span>
                          )}
                          <span className="text-muted-foreground">
                            [{m.link_type}]
                          </span>
                        </div>
                      ))}
                      {isCompleted && (
                        <div className="text-green-400 mt-1">✓ Item completed</div>
                      )}
                    </div>
                  }
                >
                  <Target
                    className={`h-3.5 w-3.5 cursor-help ${
                      hasPastDue ? 'text-destructive' : 'text-muted-foreground'
                    }`}
                  />
                </TooltipWrapper>
              )}
            </div>
          )
        },
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

    // Priority column
    baseColumns.push({
      id: 'priority',
      header: 'Priority',
      accessorKey: 'priority',
      filterType: 'select',
      filterOptions: PRIORITIES,
      helpText: 'Task priority level.',
      cell: (value) => {
        const priority = (value as string) || 'medium'
        const priorityColors: Record<string, string> = {
          critical: 'bg-red-500 text-white',
          high: 'bg-orange-500 text-white',
          medium: 'bg-yellow-500 text-black',
          low: 'bg-green-500 text-white',
        }
        return (
          <Badge className={`text-xs ${priorityColors[priority]}`}>
            {priority.charAt(0).toUpperCase() + priority.slice(1)}
          </Badge>
        )
      },
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
        id: 'actions',
        header: 'Actions',
        accessorKey: 'id',
        filterType: 'none',
        enableSorting: false,
        cell: (_, tracker) => {
          const canToggleProd = tracker.production_status === 'completed' && tracker.qc_status === 'completed'
          const isInProduction = tracker.in_production_flag
          
          return (
            <div className="flex items-center justify-end gap-2">
              {/* In Production Toggle */}
              <TooltipWrapper 
                content={canToggleProd 
                  ? (isInProduction ? 'In Production - Click to toggle' : 'Not In Production - Click to toggle')
                  : 'Both Prod and QC must be completed to toggle'}
              >
                <label className="flex cursor-pointer select-none items-center">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={isInProduction}
                      onChange={(e) => {
                        e.stopPropagation()
                        if (!isInProduction && !canToggleProd) {
                          toast.error('Both Production and QC must be Completed to set In Production flag')
                          return
                        }
                        handleProductionFlagToggle(tracker.id, !isInProduction)
                      }}
                      className="sr-only"
                      disabled={!canToggleProd && !isInProduction}
                    />
                    <div
                      className={`box block h-5 w-9 rounded-full transition-colors ${
                        isInProduction ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                      } ${!canToggleProd && !isInProduction ? 'opacity-50 cursor-not-allowed' : ''}`}
                    />
                    <div
                      className={`absolute left-0.5 top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-white shadow transition-transform ${
                        isInProduction ? 'translate-x-4' : ''
                      }`}
                    >
                      <Factory className={`h-2.5 w-2.5 ${isInProduction ? 'text-green-500' : 'text-gray-400'}`} />
                    </div>
                  </div>
                </label>
              </TooltipWrapper>

              {/* Comments Button */}
              <TooltipWrapper 
                content={`Comments: ${tracker.comment_count || 0} total, ${tracker.unresolved_comment_count || 0} unresolved`}
              >
                <Button variant="ghost" size="icon" onClick={() => handleOpenComments(tracker)} className="relative h-8 w-8">
                  <MessageSquare className="h-4 w-4" />
                  {(tracker.unresolved_comment_count || 0) > 0 && (
                    <span className="absolute -top-1 -right-1 bg-destructive text-destructive-foreground text-xs rounded-full h-4 w-4 flex items-center justify-center">
                      {tracker.unresolved_comment_count}
                    </span>
                  )}
                </Button>
              </TooltipWrapper>
              
              {/* Edit Button */}
              <TooltipWrapper content="Edit tracker">
                <Button variant="ghost" size="icon" onClick={() => handleEdit(tracker)} className="h-8 w-8">
                  <Edit className="h-4 w-4" />
                </Button>
              </TooltipWrapper>
              
              {/* Delete Button */}
              <TooltipWrapper content="Delete tracker">
                <Button variant="ghost" size="icon" onClick={() => handleDelete(tracker)} className="h-8 w-8">
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </TooltipWrapper>
            </div>
          )
        },
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
                Manage programmer assignments, status tracking, and tags. Use checkboxes to select items for bulk updates.
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
            {selectedRows.size > 0 && canBulkAssign && (
              <>
                <TooltipWrapper content={`Assign tag to ${selectedRows.size} selected trackers`}>
                  <Button variant="outline" size="sm" onClick={() => setBulkTagOpen(true)}>
                    <Tag className="h-4 w-4 mr-2" />
                    Tag ({selectedRows.size})
                  </Button>
                </TooltipWrapper>
                {availableMilestones.length > 0 && (
                  <TooltipWrapper content={`Assign milestone to ${selectedRows.size} selected trackers`}>
                    <Button variant="outline" size="sm" onClick={() => setBulkMilestoneOpen(true)}>
                      <Target className="h-4 w-4 mr-2" />
                      Milestone ({selectedRows.size})
                    </Button>
                  </TooltipWrapper>
                )}
                <TooltipWrapper content={`Assign programmers and update status for ${selectedRows.size} selected trackers`}>
                  <Button variant="outline" size="sm" onClick={() => setBulkAssignStatusOpen(true)}>
                    <UserCheck className="h-4 w-4 mr-2" />
                    Assign & Update ({selectedRows.size})
                  </Button>
                </TooltipWrapper>
              </>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4 flex-wrap">
            <div className="w-56">
              <Label className="text-sm font-medium mb-1.5 block">Study</Label>
              <Select 
                value={selectedStudyId} 
                onValueChange={(v) => { 
                  setSelectedStudyId(v)
                  setSelectedReleaseId('')
                  setSelectedEffortId('')
                  setSelectedRows(new Set())
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a study" />
                </SelectTrigger>
                <SelectContent>
                  {studies.map((study) => (
                    <SelectItem key={study.id} value={String(study.id)}>
                      {study.study_label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedStudyId && (
              <div className="w-56">
                <Label className="text-sm font-medium mb-1.5 block">Database Release</Label>
                <Select 
                  value={selectedReleaseId} 
                  onValueChange={(v) => { 
                    setSelectedReleaseId(v)
                    setSelectedEffortId('')
                    setSelectedRows(new Set())
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a database release" />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredReleases.map((release) => (
                      <SelectItem key={release.id} value={String(release.id)}>
                        {release.database_release_label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {selectedReleaseId && (
              <div className="w-56">
                <Label className="text-sm font-medium mb-1.5 block">Reporting Effort</Label>
                <Select 
                  value={selectedEffortId} 
                  onValueChange={(v) => { 
                    setSelectedEffortId(v)
                    setSelectedRows(new Set())
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a reporting effort" />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredEfforts.map((effort) => (
                      <SelectItem key={effort.id} value={String(effort.id)}>
                        {effort.database_release_label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            
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
                {availableMilestones.length > 0 && (
                  <div className="w-52">
                    <Label>Milestone Filter</Label>
                    <Select value={milestoneFilter?.toString() || 'all'} onValueChange={(v) => setMilestoneFilter(v === 'all' ? null : Number(v))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Milestones</SelectItem>
                        {phases.map((phase) => (
                          <div key={phase.id}>
                            <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground">
                              {phase.name}
                            </div>
                            {(phase.milestones || []).map((milestone) => (
                              <SelectItem key={milestone.id} value={String(milestone.id)}>
                                <div className="flex items-center gap-2">
                                  <Target className="h-3 w-3" />
                                  <span className="truncate">{milestone.name}</span>
                                </div>
                              </SelectItem>
                            ))}
                          </div>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Use Cases Display - shows when effort is selected */}
          {selectedEffortId && (() => {
            const currentEffort = efforts.find(e => String(e.id) === selectedEffortId)
            const useCases = currentEffort?.use_cases || []
            if (useCases.length === 0) return null
            return (
              <div className="flex items-center gap-2 mb-4">
                <span className="text-sm text-muted-foreground">Use Cases:</span>
                <div className="flex flex-wrap gap-1">
                  {useCases.map((uc: { id: number; name: string; color: string }) => (
                    <span
                      key={uc.id}
                      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                      style={{ backgroundColor: `${uc.color}20`, color: uc.color }}
                    >
                      {uc.name}
                    </span>
                  ))}
                </div>
              </div>
            )
          })()}

          {/* Milestones Section - shows when effort is selected */}
          {selectedEffortId && (
            <Accordion type="single" collapsible className="mb-4">
              <AccordionItem value="milestones" className="border rounded-lg">
                <AccordionTrigger className="px-4 hover:no-underline">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    <span>Project Milestones</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  <MilestoneEditor
                    reportingEffortId={Number(selectedEffortId)}
                    reportingEffortLabel={filteredEfforts.find(e => String(e.id) === selectedEffortId)?.database_release_label}
                  />
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}

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
              {/* Tabs Header - only in list view */}
              {viewMode === 'list' && (
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
              )}

              {/* View Toggle and My Tasks Filter */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Button
                    variant={taskFilter === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setTaskFilter('all')}
                  >
                    <Users className="h-4 w-4 mr-1" />
                    All Tasks
                  </Button>
                  <Button
                    variant={taskFilter === 'my-tasks' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setTaskFilter('my-tasks')}
                  >
                    <UserCheck className="h-4 w-4 mr-1" />
                    My Tasks
                  </Button>
                </div>

                {/* Item code filter indicator - inline between task filter and view toggle */}
                {itemCodeFilter && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border-2 border-blue-500 bg-blue-50 dark:bg-blue-950/30">
                    <Target className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    <span className="text-sm text-blue-700 dark:text-blue-300">
                      Filtered: <strong className="font-mono">{itemCodeFilter}</strong>
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 text-blue-600 hover:text-blue-800 hover:bg-blue-100 dark:text-blue-400 dark:hover:bg-blue-900"
                      onClick={() => setItemCodeFilter(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                )}
                
                <div className="flex items-center gap-2">
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('list')}
                  >
                    <LayoutList className="h-4 w-4 mr-1" />
                    List
                  </Button>
                  <Button
                    variant={viewMode === 'kanban-prod' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('kanban-prod')}
                  >
                    <Kanban className="h-4 w-4 mr-1" />
                    Prod Kanban
                  </Button>
                  <Button
                    variant={viewMode === 'kanban-qc' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('kanban-qc')}
                  >
                    <Kanban className="h-4 w-4 mr-1" />
                    QC Kanban
                  </Button>
                </div>
              </div>

              {/* Kanban Views */}
              {viewMode === 'kanban-prod' && (
                <div className="mb-4">
                  <h3 className="text-lg font-medium mb-2">Production Kanban</h3>
                  <KanbanBoard 
                    trackers={filteredTrackers} 
                    statusField="production"
                    onCardClick={(tracker) => {
                      // Permission check: Only production programmer, admin, or study lead can interact in Prod Kanban
                      const isAdmin = currentUser?.is_admin
                      const isProductionProgrammer = currentUser && tracker.production_programmer_id === currentUser.id
                      if (!isAdmin && !isStudyLead && !isProductionProgrammer) {
                        toast.error('Only the assigned production programmer or study lead can view/edit this task in Production Kanban')
                        return
                      }
                      setSelectedTracker(tracker)
                      setCommentDialogContext('production')
                      setCommentDialogOpen(true)
                    }}
                    onStatusChange={(trackerId, newStatus) => {
                      // Find the tracker to validate the update
                      const tracker = trackers.find(t => t.id === trackerId)
                      if (!tracker) return
                      
                      // Permission check: Only production programmer, admin, or study lead can change production status
                      const isAdmin = currentUser?.is_admin
                      const isProductionProgrammer = currentUser && tracker.production_programmer_id === currentUser.id
                      if (!isAdmin && !isStudyLead && !isProductionProgrammer) {
                        toast.error('Only the assigned production programmer or study lead can change production status')
                        return
                      }
                      
                      // Validate: production programmer must be assigned to change status (except not_started)
                      if (newStatus !== 'not_started' && !tracker.production_programmer_id) {
                        toast.error('Cannot change status without a production programmer assigned')
                        return
                      }
                      
                      // Validate: Cannot set production status to 'completed' directly - it's auto-set by QC completion
                      if (newStatus === 'completed') {
                        toast.error("Production status cannot be set to 'Completed' directly. It is automatically set when QC marks the item as completed.")
                        return
                      }
                      
                      // Update the tracker via API
                      updateTracker.mutate({
                        id: trackerId,
                        data: { production_status: newStatus as ProductionStatus }
                      })
                    }}
                    onProductionFlagToggle={handleProductionFlagToggle}
                  />
                </div>
              )}
              
              {viewMode === 'kanban-qc' && (
                <div className="mb-4">
                  <h3 className="text-lg font-medium mb-2">QC Kanban</h3>
                  <KanbanBoard 
                    trackers={filteredTrackers} 
                    statusField="qc"
                    onCardClick={(tracker) => {
                      // Permission check: Only QC programmer, admin, or study lead can interact in QC Kanban
                      const isAdmin = currentUser?.is_admin
                      const isQCProgrammer = currentUser && tracker.qc_programmer_id === currentUser.id
                      if (!isAdmin && !isStudyLead && !isQCProgrammer) {
                        toast.error('Only the assigned QC programmer or study lead can view/edit this task in QC Kanban')
                        return
                      }
                      setSelectedTracker(tracker)
                      setCommentDialogContext('qc')
                      setCommentDialogOpen(true)
                    }}
                    onStatusChange={(trackerId, newStatus) => {
                      // Find the tracker to validate the update
                      const tracker = trackers.find(t => t.id === trackerId)
                      if (!tracker) return
                      
                      // Permission check: Only QC programmer, admin, or study lead can change QC status
                      const isAdmin = currentUser?.is_admin
                      const isQCProgrammer = currentUser && tracker.qc_programmer_id === currentUser.id
                      if (!isAdmin && !isStudyLead && !isQCProgrammer) {
                        toast.error('Only the assigned QC programmer or study lead can change QC status')
                        return
                      }
                      
                      // Validate: QC programmer must be assigned to change status (except not_started)
                      if (newStatus !== 'not_started' && !tracker.qc_programmer_id) {
                        toast.error('Cannot change status without a QC programmer assigned')
                        return
                      }
                      
                      // Validate: QC 'completed' or 'failed' only allowed when production is 'ready_for_qc'
                      if ((newStatus === 'completed' || newStatus === 'failed') && tracker.production_status !== 'ready_for_qc') {
                        toast.error(`QC can only be marked as '${newStatus === 'completed' ? 'Completed' : 'Failed'}' when production status is 'Ready for QC'`)
                        return
                      }
                      
                      // Validate: Cannot mark QC as completed if there are unresolved comments
                      if (newStatus === 'completed' && (tracker.unresolved_comment_count || 0) > 0) {
                        toast.error(`Cannot mark QC as completed: ${tracker.unresolved_comment_count} unresolved comment(s) must be addressed first`)
                        return
                      }
                      
                      // If changing to 'failed', show comment dialog instead of direct update
                      if (newStatus === 'failed') {
                        setQcFailureTrackerId(trackerId)
                        setQcFailureTrackerCode(tracker.item_code)
                        setQcFailureDialogOpen(true)
                        return
                      }
                      
                      // Update the tracker via API
                      updateTracker.mutate({
                        id: trackerId,
                        data: { qc_status: newStatus as QCStatus }
                      })
                    }}
                    onProductionFlagToggle={handleProductionFlagToggle}
                  />
                </div>
              )}

              {/* List View Content */}
              {viewMode === 'list' && (
                <>
                  {/* Bulk operations hint - show when items exist but none selected */}
                  {filteredTrackers.length > 0 && selectedRows.size === 0 && canBulkAssign && (
                    <div className="flex items-center gap-2 p-3 mb-4 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-700 dark:text-blue-300">
                      <CheckSquare className="h-4 w-4 flex-shrink-0" />
                      <span>
                        <strong>Tip:</strong> Use the checkboxes in the first column to select multiple items, then click <strong>"Tag"</strong>, <strong>"Milestone"</strong>, or <strong>"Assign & Update"</strong> buttons to perform bulk operations.
                      </span>
                    </div>
                  )}
                  
                  {/* Selection count indicator - show when items are selected */}
                  {selectedRows.size > 0 && (
                    <div className="flex items-center justify-between p-3 mb-4 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg text-sm text-green-700 dark:text-green-300">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 flex-shrink-0" />
                        <span>
                          <strong>{selectedRows.size} item{selectedRows.size > 1 ? 's' : ''} selected</strong> — Ready for bulk operations
                        </span>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-7 text-green-700 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-900"
                        onClick={() => setSelectedRows(new Set())}
                      >
                        <X className="h-4 w-4 mr-1" />
                        Clear Selection
                      </Button>
                    </div>
                  )}
                  
                  {['tlf', 'sdtm', 'adam'].map((tab) => (
                    <TabsContent key={tab} value={tab}>
                      {filteredTrackers.length === 0 ? (
                        <EmptyState
                          icon={ClipboardCheck}
                          title="No trackers found"
                          description={commentFilter !== 'all' || tagFilter !== null || milestoneFilter !== null || itemCodeFilter ? "No items match the current filters." : "No items in this tracker."}
                        />
                      ) : (
                        <DataTable data={filteredTrackers} columns={columns} />
                      )}
                    </TabsContent>
                  ))}
                </>
              )}
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
          {(() => {
            // Permission checks for Edit Dialog
            const isAdmin = currentUser?.is_admin
            const isProductionProgrammer = currentUser && selectedTracker?.production_programmer_id === currentUser.id
            const isQCProgrammer = currentUser && selectedTracker?.qc_programmer_id === currentUser.id
            // Study LEAD has full access like admin for edit operations
            const canEditProduction = isAdmin || isStudyLead || isProductionProgrammer
            const canEditQC = isAdmin || isStudyLead || isQCProgrammer
            const canAssignProgrammers = isAdmin || isStudyLead
            
            // Determine which QC statuses to show - use editFormData for current state
            // Show full QC statuses (including failed) when production is ready_for_qc OR if current QC status is already failed
            // Show full QC statuses (including failed/completed) when:
            // - Production is ready_for_qc or completed
            // - Current QC status is already failed (to allow changes)
            const showFullQCStatuses = editFormData.production_status === 'ready_for_qc' || 
                                       editFormData.production_status === 'completed' ||
                                       selectedTracker?.qc_status === 'failed' ||
                                       editFormData.qc_status === 'failed' ||
                                       selectedTracker?.qc_status === 'completed' ||
                                       editFormData.qc_status === 'completed'
            
            return (
              <div className="grid gap-4 py-4">
                {/* Programmer Assignment - Admin or Study LEAD can change */}
                {canAssignProgrammers && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label>Production Programmer</Label>
                      <Select
                        value={editFormData.production_programmer_id || 'none'}
                        onValueChange={(v) => {
                          const newProgrammerId = v === 'none' ? '' : v
                          // Auto-set due date when assigning production programmer (if not already set)
                          if (newProgrammerId && !editFormData.due_date && !selectedTracker?.due_date) {
                            setEditFormData((prev) => ({ 
                              ...prev, 
                              production_programmer_id: newProgrammerId,
                              due_date: getDefaultDueDate()
                            }))
                          } else {
                            setEditFormData((prev) => ({ ...prev, production_programmer_id: newProgrammerId }))
                          }
                        }}
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
                )}
                
                {/* Status Updates - Permission based */}
                <div className={`grid gap-4 ${canEditProduction && canEditQC ? 'grid-cols-2' : 'grid-cols-1'}`}>
                  {canEditProduction && (
                    <div className="grid gap-2">
                      <Label>Production Status</Label>
                      <Select
                        value={editFormData.production_status}
                        onValueChange={(v: ProductionStatus) => setEditFormData((prev) => ({ ...prev, production_status: v }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {/* Show PRODUCTION_STATUSES plus completed (for display when already completed) */}
                          {[...PRODUCTION_STATUSES, 'completed' as ProductionStatus].map((s) => (
                            <SelectItem 
                              key={s} 
                              value={s}
                              disabled={s === 'completed'} // Completed is auto-set by QC
                            >
                              {s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                              {s === 'completed' && ' (auto)'}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                  {canEditQC && (
                    <div className="grid gap-2">
                      <Label>QC Status</Label>
                      <Select
                        value={editFormData.qc_status}
                        onValueChange={(v: QCStatus) => setEditFormData((prev) => ({ ...prev, qc_status: v }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {/* Show full QC statuses when production is ready_for_qc or current status is failed */}
                          {(showFullQCStatuses ? QC_STATUSES_READY : QC_STATUSES).map((s) => (
                            <SelectItem 
                              key={s} 
                              value={s}
                              disabled={s === 'completed' && (selectedTracker?.unresolved_comment_count || 0) > 0}
                            >
                              {s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                              {s === 'completed' && (selectedTracker?.unresolved_comment_count || 0) > 0 && ' (resolve comments first)'}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {(selectedTracker?.unresolved_comment_count || 0) > 0 && (
                        <p className="text-xs text-muted-foreground">
                          {selectedTracker?.unresolved_comment_count} unresolved comment(s) must be addressed before QC can be completed
                        </p>
                      )}
                    </div>
                  )}
                </div>
                
                {/* No permission message */}
                {!canEditProduction && !canEditQC && (
                  <div className="text-center py-4 text-muted-foreground">
                    You don't have permission to edit this tracker's status.
                  </div>
                )}
                
                {/* Priority and Due Date - Admin, Study LEAD, and Production Programmer can edit */}
                {(isAdmin || isStudyLead || canEditProduction) && (
                  <div className="grid grid-cols-2 gap-4">
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
                      <Label>Due Date {editFormData.production_programmer_id && <span className="text-destructive">*</span>}</Label>
                      <Input
                        type="date"
                        value={editFormData.due_date}
                        onChange={(e) => setEditFormData((prev) => ({ ...prev, due_date: e.target.value }))}
                        className={editFormData.production_programmer_id && !editFormData.due_date ? 'border-destructive' : ''}
                      />
                      {editFormData.production_programmer_id && !editFormData.due_date && (
                        <p className="text-xs text-destructive">Required when production programmer is assigned</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Milestone Assignment - Admin, Study LEAD, and Production Programmer can edit */}
                {(isAdmin || isStudyLead || canEditProduction) && availableMilestones.length > 0 && (
                  <div className="grid gap-2">
                    <div className="flex items-center gap-1">
                      <Label>Milestones</Label>
                      <HelpIcon
                        content="Link this item to milestones for tracking. Items can be linked to multiple milestones. A warning will show if the item's due date is after the milestone due date."
                        side="right"
                      />
                    </div>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          role="combobox"
                          className="justify-between h-auto min-h-9"
                        >
                          {editFormData.milestone_ids.length === 0
                            ? 'Select milestones...'
                            : `${editFormData.milestone_ids.length} milestone(s) selected`}
                          <Target className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-80 p-0" align="start">
                        <ScrollArea className="h-60">
                          <div className="p-2 space-y-1">
                            {phases.map((phase) => (
                              <div key={phase.id} className="space-y-1">
                                <div className="text-xs font-medium text-muted-foreground px-2 py-1">
                                  {phase.name}
                                </div>
                                {(phase.milestones || []).map((milestone) => {
                                  const isSelected = editFormData.milestone_ids.includes(milestone.id)
                                  return (
                                    <div
                                      key={milestone.id}
                                      className={`flex items-center gap-2 px-2 py-1.5 rounded-sm cursor-pointer hover:bg-accent ${
                                        isSelected ? 'bg-accent' : ''
                                      }`}
                                      onClick={() => {
                                        setEditFormData((prev) => ({
                                          ...prev,
                                          milestone_ids: isSelected
                                            ? prev.milestone_ids.filter((id) => id !== milestone.id)
                                            : [...prev.milestone_ids, milestone.id],
                                        }))
                                      }}
                                    >
                                      <Checkbox checked={isSelected} />
                                      <div className="flex-1 min-w-0">
                                        <div className="text-sm truncate">{milestone.name}</div>
                                        {milestone.due_date && (
                                          <div className="text-xs text-muted-foreground">
                                            Due: {formatDate(milestone.due_date)}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  )
                                })}
                              </div>
                            ))}
                          </div>
                        </ScrollArea>
                      </PopoverContent>
                    </Popover>
                    {/* Show selected milestones as badges */}
                    {editFormData.milestone_ids.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {editFormData.milestone_ids.map((milestoneId) => {
                          const milestone = availableMilestones.find((m) => m.id === milestoneId)
                          if (!milestone) return null
                          const isPastDue = milestone.due_date && editFormData.due_date && editFormData.due_date > milestone.due_date
                          return (
                            <Badge
                              key={milestoneId}
                              variant={isPastDue ? 'destructive' : 'secondary'}
                              className="flex items-center gap-1"
                            >
                              <Target className="h-3 w-3" />
                              {milestone.name}
                              {isPastDue && <AlertTriangle className="h-3 w-3" />}
                              <X
                                className="h-3 w-3 cursor-pointer hover:text-destructive"
                                onClick={() =>
                                  setEditFormData((prev) => ({
                                    ...prev,
                                    milestone_ids: prev.milestone_ids.filter((id) => id !== milestoneId),
                                  }))
                                }
                              />
                            </Badge>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })()}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleEditSubmit}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Comments Dialog - Enhanced with status update capability */}
      <Dialog open={commentDialogOpen} onOpenChange={(open) => { setCommentDialogOpen(open); if (!open) { setReplyingTo(null); setNewComment({ text: '', type: 'PROGRAMMING', parentId: null, production_status: undefined, qc_status: undefined }) } }}>
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
                    isNested={false}
                  />
                ))}
              </div>
            )}
          </ScrollArea>

          {/* Add Comment Form with Status Update */}
          <div className="border-t pt-4 mt-4">
            {replyingTo && (
              <div className="flex items-center gap-2 mb-2 p-2 bg-muted rounded text-sm">
                <Reply className="h-4 w-4" />
                <span>Replying to {(replyingTo as any).username || replyingTo.user?.username || 'Unknown'}</span>
                <Button variant="ghost" size="sm" className="ml-auto h-6" onClick={cancelReply}>
                  <X className="h-3 w-3" />
                </Button>
              </div>
            )}
            
            {/* Status Update Section - Filter based on dialog context */}
            {!replyingTo && (() => {
              const isProductionProgrammer = currentUser && selectedTracker?.production_programmer_id === currentUser.id
              const isQCProgrammer = currentUser && selectedTracker?.qc_programmer_id === currentUser.id
              const isAdmin = currentUser?.is_admin
              
              // Determine what to show based on context AND permissions
              // Study LEAD has full access like admin
              let showProduction = false
              let showQC = false
              
              if (commentDialogContext === 'production') {
                // From Prod Kanban: Only show production status if user has permission
                showProduction = isProductionProgrammer || isAdmin || isStudyLead
              } else if (commentDialogContext === 'qc') {
                // From QC Kanban: Only show QC status if user has permission
                showQC = isQCProgrammer || isAdmin || isStudyLead
              } else {
                // From List view: Show both based on permissions
                showProduction = isProductionProgrammer || isAdmin || isStudyLead
                showQC = isQCProgrammer || isAdmin || isStudyLead
              }
              
              if (!showProduction && !showQC) return null
              
              const hasStatusChange = newComment.production_status || newComment.qc_status
              
              return (
                <div className="mb-4 p-3 bg-muted/30 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">
                      {commentDialogContext === 'production' ? 'Update Production Status' : 
                       commentDialogContext === 'qc' ? 'Update QC Status' : 
                       'Update Status'}
                    </Label>
                    {hasStatusChange && (
                      <Button 
                        size="sm" 
                        variant="secondary"
                        onClick={() => {
                          // Update status without requiring a comment
                          if (!selectedTracker) return
                          
                          // Handle QC Failed specially
                          if (newComment.qc_status === 'failed') {
                            setQcFailureTrackerId(selectedTracker.id)
                            setQcFailureTrackerCode(selectedTracker.item_code)
                            setQcFailureDialogOpen(true)
                            setCommentDialogOpen(false)
                            return
                          }
                          
                          const updateData: any = {}
                          if (newComment.production_status) updateData.production_status = newComment.production_status
                          if (newComment.qc_status) updateData.qc_status = newComment.qc_status
                          
                          updateTracker.mutate({
                            id: selectedTracker.id,
                            data: updateData
                          }, {
                            onSuccess: () => {
                              setNewComment(prev => ({ ...prev, production_status: undefined, qc_status: undefined }))
                              toast.success('Status updated')
                            }
                          })
                        }}
                      >
                        Save Status
                      </Button>
                    )}
                  </div>
                  <div className={`grid gap-4 ${showProduction && showQC ? 'grid-cols-2' : 'grid-cols-1'}`}>
                    {showProduction && (
                      <div className="space-y-1">
                        <Label className="text-xs font-medium text-muted-foreground">
                          Production Status
                        </Label>
                        <Select
                          value={newComment.production_status || '__none__'}
                          onValueChange={(v) => setNewComment((prev) => ({ 
                            ...prev, 
                            production_status: v === '__none__' ? undefined : v as ProductionStatus 
                          }))}
                        >
                          <SelectTrigger className="h-8">
                            <SelectValue placeholder="No change" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="__none__">No change</SelectItem>
                            {PRODUCTION_STATUSES.map((s) => (
                              <SelectItem key={s} value={s}>
                                {s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                    {showQC && (
                      <div className="space-y-1">
                        <Label className="text-xs font-medium text-muted-foreground">
                          QC Status
                        </Label>
                        <Select
                          value={newComment.qc_status || '__none__'}
                          onValueChange={(v) => setNewComment((prev) => ({ 
                            ...prev, 
                            qc_status: v === '__none__' ? undefined : v as QCStatus 
                          }))}
                        >
                          <SelectTrigger className="h-8">
                            <SelectValue placeholder="No change" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="__none__">No change</SelectItem>
                            {/* Show full QC statuses when production is ready_for_qc */}
                            {(selectedTracker?.production_status === 'ready_for_qc' ? QC_STATUSES_READY : QC_STATUSES).map((s) => (
                              <SelectItem 
                                key={s} 
                                value={s}
                                disabled={s === 'completed' && (selectedTracker?.unresolved_comment_count || 0) > 0}
                              >
                                {s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                                {s === 'completed' && (selectedTracker?.unresolved_comment_count || 0) > 0 && ' (resolve comments first)'}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        {(selectedTracker?.unresolved_comment_count || 0) > 0 && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Resolve {selectedTracker?.unresolved_comment_count} comment(s) to enable QC completion
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })()}
            
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
            {(newComment.production_status || newComment.qc_status) && (
              <p className="text-xs text-muted-foreground mt-2">
                Status will be updated when you submit this comment.
              </p>
            )}
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

      {/* Bulk Milestone Assignment Dialog */}
      <Dialog open={bulkMilestoneOpen} onOpenChange={(open) => {
        setBulkMilestoneOpen(open)
        if (!open) setBulkMilestoneId(null)
      }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Assign Milestone
            </DialogTitle>
            <DialogDescription>
              Link {selectedRows.size} selected tracker(s) to a milestone.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Select Milestone</Label>
              <Select
                value={bulkMilestoneId?.toString() || ''}
                onValueChange={(v) => setBulkMilestoneId(Number(v))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choose a milestone" />
                </SelectTrigger>
                <SelectContent>
                  {phases.map((phase) => (
                    <div key={phase.id}>
                      <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground">
                        {phase.name}
                      </div>
                      {(phase.milestones || []).map((milestone) => (
                        <SelectItem key={milestone.id} value={String(milestone.id)}>
                          <div className="flex items-center justify-between gap-2">
                            <span>{milestone.name}</span>
                            {milestone.due_date && (
                              <span className="text-xs text-muted-foreground">
                                Due: {formatDate(milestone.due_date)}
                              </span>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </div>
                  ))}
                </SelectContent>
              </Select>
              {bulkMilestoneId && (
                <p className="text-xs text-muted-foreground">
                  This will add the selected trackers to the milestone. Existing milestone links are preserved.
                </p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkMilestoneOpen(false)}>Cancel</Button>
            <Button
              onClick={() => {
                if (bulkMilestoneId) {
                  bulkAssignMilestone.mutate({
                    milestoneId: bulkMilestoneId,
                    trackerIds: Array.from(selectedRows),
                  })
                }
              }}
              disabled={!bulkMilestoneId || bulkAssignMilestone.isPending}
            >
              {bulkAssignMilestone.isPending ? 'Assigning...' : 'Assign'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Unified Bulk Assign & Status Dialog */}
      <Dialog open={bulkAssignStatusOpen} onOpenChange={(open) => {
        setBulkAssignStatusOpen(open)
        if (!open) {
          setBulkData({
            production_programmer_id: '',
            qc_programmer_id: '',
            production_status: '',
            qc_status: '',
            due_date: '',
            priority: '',
          })
        }
      }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Assign & Update Status</DialogTitle>
            <DialogDescription>
              Update {selectedRows.size} selected tracker(s). Assign programmers and/or update their statuses.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-6 py-4">
            {/* Production Section */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Users className="h-4 w-4" />
                Production
              </h4>
              <div className="grid gap-3 pl-6">
                <div className="grid gap-1.5">
                  <Label className="text-xs text-muted-foreground">Programmer</Label>
                  <Select
                    value={bulkData.production_programmer_id || '__none__'}
                    onValueChange={(v) => setBulkData((prev) => ({ ...prev, production_programmer_id: v === '__none__' ? '' : v }))}
                  >
                    <SelectTrigger><SelectValue placeholder="Select production programmer (optional)" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">-- No change --</SelectItem>
                      {programmers.map((p) => (
                        <SelectItem key={p.id} value={String(p.id)}>{p.username}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-1.5">
                  <Label className="text-xs text-muted-foreground">Status</Label>
                  <Select
                    value={bulkData.production_status || '__none__'}
                    onValueChange={(v) => setBulkData((prev) => ({ ...prev, production_status: v === '__none__' ? '' : v as ProductionStatus }))}
                  >
                    <SelectTrigger><SelectValue placeholder="Select status (optional)" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">-- No change --</SelectItem>
                      {PRODUCTION_STATUSES.map((s) => (
                        <SelectItem key={s} value={s}>{s.replace(/_/g, ' ')}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {bulkData.production_status && !bulkData.production_programmer_id && (
                    <p className="text-xs text-amber-600 dark:text-amber-400">
                      ⚠ Status will only update for trackers that already have a production programmer assigned
                    </p>
                  )}
                </div>
                {/* Due Date - shown when assigning production programmer */}
                {bulkData.production_programmer_id && (
                  <div className="grid gap-1.5">
                    <Label className="text-xs text-muted-foreground">Due Date</Label>
                    <Input
                      type="date"
                      value={bulkData.due_date || getDefaultDueDate()}
                      onChange={(e) => setBulkData((prev) => ({ ...prev, due_date: e.target.value }))}
                      className="h-9"
                    />
                    <p className="text-xs text-muted-foreground">
                      Default: today + 7 days. Will only update trackers without an existing due date.
                    </p>
                  </div>
                )}
              </div>
            </div>
            
            {/* QC Section */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                QC
              </h4>
              <div className="grid gap-3 pl-6">
                <div className="grid gap-1.5">
                  <Label className="text-xs text-muted-foreground">Programmer</Label>
                  <Select
                    value={bulkData.qc_programmer_id || '__none__'}
                    onValueChange={(v) => setBulkData((prev) => ({ ...prev, qc_programmer_id: v === '__none__' ? '' : v }))}
                  >
                    <SelectTrigger><SelectValue placeholder="Select QC programmer (optional)" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">-- No change --</SelectItem>
                      {programmers.map((p) => (
                        <SelectItem key={p.id} value={String(p.id)}>{p.username}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-1.5">
                  <Label className="text-xs text-muted-foreground">Status</Label>
                  <Select
                    value={bulkData.qc_status || '__none__'}
                    onValueChange={(v) => setBulkData((prev) => ({ ...prev, qc_status: v === '__none__' ? '' : v as QCStatus }))}
                  >
                    <SelectTrigger><SelectValue placeholder="Select status (optional)" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">-- No change --</SelectItem>
                      {QC_STATUSES_READY.map((s) => (
                        <SelectItem key={s} value={s}>{s.replace(/_/g, ' ')}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {bulkData.qc_status && !bulkData.qc_programmer_id && (
                    <p className="text-xs text-amber-600 dark:text-amber-400">
                      ⚠ Status will only update for trackers that already have a QC programmer assigned
                    </p>
                  )}
                </div>
              </div>
            </div>
            
            {/* Priority Section */}
            <div className="border-t pt-4 mt-2">
              <div className="grid gap-1.5">
                <Label className="text-sm font-medium">Priority (optional)</Label>
                <Select
                  value={bulkData.priority || '__none__'}
                  onValueChange={(v) => setBulkData((prev) => ({ ...prev, priority: v === '__none__' ? '' : v as Priority }))}
                >
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Select priority" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">-- No change --</SelectItem>
                    {PRIORITIES.map((p) => (
                      <SelectItem key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkAssignStatusOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleBulkAssignStatus} 
              disabled={!hasBulkChanges || bulkAssignStatus.isPending}
            >
              {bulkAssignStatus.isPending ? 'Updating...' : 'Apply Changes'}
            </Button>
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

      {/* QC Failure Comment Dialog */}
      <QCFailureCommentDialog
        trackerId={qcFailureTrackerId}
        trackerItemCode={qcFailureTrackerCode}
        effortId={selectedEffortId ? Number(selectedEffortId) : null}
        isOpen={qcFailureDialogOpen}
        onClose={() => {
          setQcFailureDialogOpen(false)
          setQcFailureTrackerId(null)
          setQcFailureTrackerCode(undefined)
        }}
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
  isNested = false
}: { 
  comment: TrackerComment
  onResolve: () => void
  onReply: (comment: TrackerComment) => void
  isNested?: boolean
}) {
  return (
    <div className={`p-3 rounded-lg border ${comment.is_resolved ? 'bg-muted/50 opacity-70' : 'bg-card'} ${isNested ? 'ml-6 mt-2' : ''}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="font-semibold text-sm">{(comment as any).username || comment.user?.username || 'Unknown'}</span>
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
              isNested={true}
            />
          ))}
        </div>
      )}
    </div>
  )
}
