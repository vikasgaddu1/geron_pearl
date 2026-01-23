import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { GitBranch, Plus, Edit, Trash2, RefreshCw, ChevronRight, ChevronDown, Folder, FolderOpen, FileText, Users, Upload, Tag, X, Lock, Unlock, History, FileSignature, Shield } from 'lucide-react'
import { toast } from 'sonner'
import { studiesApi, databaseReleasesApi, reportingEffortsApi, useCasesApi, tenantDataApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { ExcelUpload } from '@/components/common/ExcelUpload'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { TooltipWrapper } from '@/components/common/TooltipWrapper'
import { useWebSocketRefresh } from '@/hooks/useWebSocket'
import { useAuthStore } from '@/stores/authStore'
import { StudyMembersDialog } from './StudyMembersDialog'
import { LockReportingEffortDialog } from './LockReportingEffortDialog'
import { LockHistoryDialog } from './LockHistoryDialog'
import { SignReportingEffortDialog } from './SignReportingEffortDialog'
import { SignatureSetupDialog } from '../settings/SignatureSetupDialog'
import type { Study, DatabaseRelease, ReportingEffort, BulkHierarchyRow, UseCase, UseCaseSummary } from '@/types'
import { cn, getErrorMessage } from '@/lib/utils'

type NodeType = 'study' | 'release' | 'effort'

interface TreeNode {
  id: number
  type: NodeType
  label: string
  children?: TreeNode[]
  data: Study | DatabaseRelease | ReportingEffort
}

export function StudyManagement() {
  const queryClient = useQueryClient()
  const { currentUser, isResponsibleForStudy } = useAuthStore()
  const isGlobalAdmin = currentUser?.is_admin === true
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState<'add-study' | 'add-release' | 'add-effort' | 'edit'>('add-study')
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [membersDialogOpen, setMembersDialogOpen] = useState(false)
  const [bulkUploadOpen, setBulkUploadOpen] = useState(false)
  const [useCasesDialogOpen, setUseCasesDialogOpen] = useState(false)
  const [lockDialogOpen, setLockDialogOpen] = useState(false)
  const [lockHistoryDialogOpen, setLockHistoryDialogOpen] = useState(false)
  const [signDialogOpen, setSignDialogOpen] = useState(false)
  const [signatureSetupDialogOpen, setSignatureSetupDialogOpen] = useState(false)
  const [formData, setFormData] = useState({ label: '', date: '' })

  const formatDateForInput = (value?: string) => (value ? value.slice(0, 10) : '')

  // Queries
  const { data: studies = [], isLoading: studiesLoading } = useQuery({
    queryKey: ['studies'],
    queryFn: studiesApi.getAll,
  })

  const { data: releases = [] } = useQuery({
    queryKey: ['database-releases'],
    queryFn: databaseReleasesApi.getAll,
  })

  const { data: efforts = [] } = useQuery({
    queryKey: ['reporting-efforts'],
    queryFn: reportingEffortsApi.getAll,
  })

  // Query for all available use cases
  const { data: allUseCases = [] } = useQuery({
    queryKey: ['use-cases'],
    queryFn: useCasesApi.getAllUseCases,
  })

  // Query for study permissions (when a study is selected)
  const selectedStudyId = selectedNode?.type === 'study' ? selectedNode.id : null
  const { data: studyPermissions } = useQuery({
    queryKey: ['study-permissions', selectedStudyId],
    queryFn: () => studiesApi.getMyPermissions(selectedStudyId!),
    enabled: !!selectedStudyId && !!currentUser,
  })

  // Query for tenant signature lock setting
  // When true: signing auto-locks (hide manual lock toggle)
  // When false: manual lock/unlock is available
  const { data: signatureLockSetting } = useQuery({
    queryKey: ['tenant-signature-lock-setting'],
    queryFn: tenantDataApi.getSignatureLockSetting,
  })
  const showManualLockToggle = signatureLockSetting?.signature_locks_effort === false

  // Check if current user can manage members (LEAD or global ADMIN)
  const canManageMembers = currentUser?.is_admin || studyPermissions?.can_manage_members

  // WebSocket refresh
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['studies'] })
    queryClient.invalidateQueries({ queryKey: ['database-releases'] })
    queryClient.invalidateQueries({ queryKey: ['reporting-efforts'] })
  }, [queryClient])

  useWebSocketRefresh(['study', 'database_release', 'reporting_effort'], refetch)

  // Mutations
  const createStudy = useMutation({
    mutationFn: studiesApi.create,
    onSuccess: () => {
      toast.success('Study created successfully')
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      setDialogOpen(false)
    },
    onError: (error) => toast.error(`Failed to create study: ${getErrorMessage(error)}`),
  })

  const updateStudy = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { study_label: string } }) =>
      studiesApi.update(id, data),
    onSuccess: (updatedStudy) => {
      toast.success('Study updated successfully')
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      // Update selectedNode with fresh data
      if (selectedNode?.type === 'study' && selectedNode.id === updatedStudy.id) {
        setSelectedNode({
          ...selectedNode,
          label: updatedStudy.study_label,
          data: updatedStudy,
        })
      }
      setDialogOpen(false)
    },
    onError: (error) => toast.error(`Failed to update study: ${getErrorMessage(error)}`),
  })

  const deleteStudy = useMutation({
    mutationFn: studiesApi.delete,
    onSuccess: () => {
      toast.success('Study deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      setSelectedNode(null)
    },
    onError: (error) => toast.error(`Failed to delete study: ${getErrorMessage(error)}`),
  })

  const createRelease = useMutation({
    mutationFn: databaseReleasesApi.create,
    onSuccess: () => {
      toast.success('Database release created successfully')
      queryClient.invalidateQueries({ queryKey: ['database-releases'] })
      setDialogOpen(false)
    },
    onError: (error) => toast.error(`Failed to create database release: ${getErrorMessage(error)}`),
  })

  const updateRelease = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { database_release_label: string; database_release_date?: string } }) =>
      databaseReleasesApi.update(id, data),
    onSuccess: (updatedRelease) => {
      toast.success('Database release updated successfully')
      queryClient.invalidateQueries({ queryKey: ['database-releases'] })
      // Update selectedNode with fresh data
      if (selectedNode?.type === 'release' && selectedNode.id === updatedRelease.id) {
        setSelectedNode({
          ...selectedNode,
          label: updatedRelease.database_release_label,
          data: updatedRelease,
        })
      }
      setDialogOpen(false)
    },
    onError: (error) => toast.error(`Failed to update database release: ${getErrorMessage(error)}`),
  })

  const createEffort = useMutation({
    mutationFn: reportingEffortsApi.create,
    onSuccess: () => {
      toast.success('Reporting effort created successfully')
      queryClient.invalidateQueries({ queryKey: ['reporting-efforts'] })
      setDialogOpen(false)
    },
    onError: (error) => toast.error(`Failed to create reporting effort: ${getErrorMessage(error)}`),
  })

  const updateEffort = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { database_release_label?: string } }) =>
      reportingEffortsApi.update(id, data),
    onSuccess: (updatedEffort) => {
      toast.success('Reporting effort updated successfully')
      queryClient.invalidateQueries({ queryKey: ['reporting-efforts'] })
      if (selectedNode?.type === 'effort' && selectedNode.id === updatedEffort.id) {
        setSelectedNode({
          ...selectedNode,
          label: updatedEffort.database_release_label,
          data: updatedEffort,
        })
      }
      setDialogOpen(false)
    },
    onError: (error) => toast.error(`Failed to update reporting effort: ${getErrorMessage(error)}`),
  })

  // Use case assignment mutations
  const assignUseCase = useMutation({
    mutationFn: ({ reportingEffortId, useCaseId }: { reportingEffortId: number; useCaseId: number }) =>
      useCasesApi.assignUseCase(reportingEffortId, useCaseId),
    onSuccess: () => {
      toast.success('Use case assigned')
      queryClient.invalidateQueries({ queryKey: ['reporting-efforts'] })
    },
    onError: (error) => toast.error(`Failed to assign use case: ${getErrorMessage(error)}`),
  })

  const removeUseCaseAssignment = useMutation({
    mutationFn: ({ reportingEffortId, useCaseId }: { reportingEffortId: number; useCaseId: number }) =>
      useCasesApi.removeUseCaseAssignment(reportingEffortId, useCaseId),
    onSuccess: () => {
      toast.success('Use case removed')
      queryClient.invalidateQueries({ queryKey: ['reporting-efforts'] })
    },
    onError: (error) => toast.error(`Failed to remove use case: ${getErrorMessage(error)}`),
  })

  const bulkUploadHierarchy = useMutation({
    mutationFn: (rows: BulkHierarchyRow[]) => studiesApi.bulkHierarchyUpload(rows),
    onSuccess: (result) => {
      toast.success(
        `Bulk upload done. Studies: +${result.created_studies}, Releases: +${result.created_releases}, Efforts: +${result.created_efforts}, skipped duplicates: ${result.skipped_duplicates}`
      )
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      queryClient.invalidateQueries({ queryKey: ['database-releases'] })
      queryClient.invalidateQueries({ queryKey: ['reporting-efforts'] })
      setBulkUploadOpen(false)
    },
    onError: (error) => toast.error(`Bulk upload failed: ${getErrorMessage(error)}`),
  })

  // Build tree structure - filter studies based on user role
  const buildTree = (): TreeNode[] => {
    // For global admins, show all studies
    // For responsible users, only show studies where they have responsible access
    const filteredStudies = isGlobalAdmin
      ? studies
      : studies.filter((study) => isResponsibleForStudy(study.id))
    
    return filteredStudies.map((study) => {
      const studyReleases = releases.filter((r) => r.study_id === study.id)
      return {
        id: study.id,
        type: 'study' as NodeType,
        label: study.study_label,
        data: study,
        children: studyReleases.map((release) => {
          const releaseEfforts = efforts.filter((e) => e.database_release_id === release.id)
          return {
            id: release.id,
            type: 'release' as NodeType,
            label: release.database_release_label,
            data: release,
            children: releaseEfforts.map((effort) => ({
              id: effort.id,
              type: 'effort' as NodeType,
              label: effort.database_release_label,
              data: effort,
            })),
          }
        }),
      }
    })
  }

  const tree = buildTree()
  
  // Check if user has permission for currently selected study
  const canEditSelectedStudy = selectedNode && (
    isGlobalAdmin ||
    (selectedNode.type === 'study' && isResponsibleForStudy(selectedNode.id)) ||
    (selectedNode.type === 'release' && isResponsibleForStudy((selectedNode.data as DatabaseRelease).study_id)) ||
    (selectedNode.type === 'effort' && isResponsibleForStudy((selectedNode.data as ReportingEffort).study_id))
  )

  const toggleNode = (nodeKey: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev)
      if (next.has(nodeKey)) {
        next.delete(nodeKey)
      } else {
        next.add(nodeKey)
      }
      return next
    })
  }

  const handleAdd = (type: 'add-study' | 'add-release' | 'add-effort') => {
    setDialogMode(type)
    setFormData({ label: '', date: '' })
    setDialogOpen(true)
  }

  const handleEdit = () => {
    if (!selectedNode) return
    setDialogMode('edit')
    if (selectedNode.type === 'study') {
      setFormData({ label: (selectedNode.data as Study).study_label, date: '' })
    } else if (selectedNode.type === 'release') {
      const release = selectedNode.data as DatabaseRelease
      setFormData({
        label: release.database_release_label,
        date: formatDateForInput(release.database_release_date),
      })
    } else {
      const effort = selectedNode.data as ReportingEffort
      setFormData({
        label: effort.database_release_label,
        date: '',
      })
    }
    setDialogOpen(true)
  }

  const handleSubmit = () => {
    if (dialogMode === 'add-study') {
      createStudy.mutate({ study_label: formData.label })
    } else if (dialogMode === 'add-release' && selectedNode?.type === 'study') {
      createRelease.mutate({
        study_id: selectedNode.id,
        database_release_label: formData.label,
        database_release_date: formData.date,
      })
    } else if (dialogMode === 'add-effort' && selectedNode?.type === 'release') {
      const release = selectedNode.data as DatabaseRelease
      createEffort.mutate({
        study_id: release.study_id,
        database_release_id: selectedNode.id,
        database_release_label: formData.label,
      })
    } else if (dialogMode === 'edit' && selectedNode) {
      if (selectedNode.type === 'study') {
        updateStudy.mutate({ id: selectedNode.id, data: { study_label: formData.label } })
      } else if (selectedNode.type === 'release') {
        updateRelease.mutate({
          id: selectedNode.id,
          data: {
            database_release_label: formData.label,
            database_release_date: formData.date || undefined,
          },
        })
      } else if (selectedNode.type === 'effort') {
        updateEffort.mutate({
          id: selectedNode.id,
          data: {
            database_release_label: formData.label,
          },
        })
      }
    }
  }

  const handleBulkUploadRows = async (rows: Record<string, string>[]) => {
    const payload: BulkHierarchyRow[] = rows.map((r) => ({
      study_label: r.study_label?.trim() || '',
      database_release_label: r.database_release_label?.trim() || '',
      reporting_effort_label: r.reporting_effort_label?.trim() || '',
    }))
    await bulkUploadHierarchy.mutateAsync(payload)
  }

  const handleDelete = () => {
    if (!selectedNode) return
    if (selectedNode.type === 'study') {
      deleteStudy.mutate(selectedNode.id)
    }
    // Add delete logic for release and effort
    setDeleteDialogOpen(false)
  }

  const renderTreeNode = (node: TreeNode, level = 0) => {
    const nodeKey = `${node.type}-${node.id}`
    const isExpanded = expandedNodes.has(nodeKey)
    const hasChildren = node.children && node.children.length > 0
    const isSelected = selectedNode?.type === node.type && selectedNode?.id === node.id
    
    // Check if user can manage members for this specific study
    const canManageMembersForStudy = node.type === 'study' && (
      isGlobalAdmin || isResponsibleForStudy(node.id)
    )

    const Icon = node.type === 'study'
      ? (isExpanded ? FolderOpen : Folder)
      : node.type === 'release'
      ? (isExpanded ? FolderOpen : Folder)
      : FileText

    return (
      <div key={nodeKey}>
        <div
          className={cn(
            'flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-colors group',
            isSelected ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
          )}
          style={{ paddingLeft: `${level * 20 + 8}px` }}
          onClick={() => setSelectedNode(node)}
        >
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleNode(nodeKey)
              }}
              className="p-0.5"
            >
              {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </button>
          ) : (
            <span className="w-5" />
          )}
          <Icon className="h-4 w-4" />
          <span className="text-sm flex-1 flex items-center gap-1.5">
            {node.label}
            {node.type === 'effort' && (node.data as ReportingEffort).is_signed && (
              <Shield className="h-3.5 w-3.5 text-green-500" title="Signed" />
            )}
            {node.type === 'effort' && (node.data as ReportingEffort).is_locked && !(node.data as ReportingEffort).is_signed && (
              <Lock className="h-3.5 w-3.5 text-amber-500" title="Locked" />
            )}
          </span>
          
          {/* Inline Manage Members button for studies */}
          {canManageMembersForStudy && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                setSelectedNode(node)
                setMembersDialogOpen(true)
              }}
              className={cn(
                'p-1.5 rounded-md transition-all',
                isSelected 
                  ? 'opacity-100 hover:bg-primary-foreground/20' 
                  : 'opacity-0 group-hover:opacity-100 hover:bg-accent-foreground/10'
              )}
              title="Manage Members"
            >
              <Users className="h-4 w-4" />
            </button>
          )}
        </div>
        {isExpanded && node.children?.map((child) => renderTreeNode(child, level + 1))}
      </div>
    )
  }

  if (studiesLoading) {
    return <PageLoader text="Loading studies..." />
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-5 w-5 text-primary" />
                Study Management
              </CardTitle>
              <CardDescription className="mt-1.5">
                Manage studies, database releases, and reporting efforts. Select a study to manage team members and permissions.
              </CardDescription>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 pt-3 border-t mt-4">
            <Button variant="outline" size="sm" onClick={refetch}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            {/* Only global admins can bulk upload or create new studies */}
            {isGlobalAdmin && (
              <>
                <Button variant="outline" size="sm" onClick={() => setBulkUploadOpen(true)}>
                  <Upload className="h-4 w-4 mr-2" />
                  Bulk Upload
                </Button>
                <Button size="sm" onClick={() => handleAdd('add-study')}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Study
                </Button>
              </>
            )}
            {/* LEAD users can add releases/efforts to their studies */}
            {selectedNode?.type === 'study' && canEditSelectedStudy && (
              <>
                <Button size="sm" variant="outline" onClick={() => handleAdd('add-release')}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Release
                </Button>
                {canManageMembers && (
                  <Button size="sm" variant="outline" onClick={() => setMembersDialogOpen(true)}>
                    <Users className="h-4 w-4 mr-2" />
                    Manage Members
                  </Button>
                )}
              </>
            )}
            {selectedNode?.type === 'release' && canEditSelectedStudy && (
              <Button size="sm" variant="outline" onClick={() => handleAdd('add-effort')}>
                <Plus className="h-4 w-4 mr-2" />
                Add Effort
              </Button>
            )}
            {selectedNode && canEditSelectedStudy && (
              <>
                <Button size="sm" variant="secondary" onClick={handleEdit}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit
                </Button>
                {/* Only global admins can delete studies; LEADs can delete releases/efforts in their studies */}
                {(isGlobalAdmin || selectedNode.type !== 'study') && (
                  <Button size="sm" variant="destructive" onClick={() => setDeleteDialogOpen(true)}>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                )}
              </>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {tree.length === 0 ? (
            <EmptyState
              icon={GitBranch}
              title="No studies found"
              description="Get started by creating your first study."
              action={{ label: 'Add Study', onClick: () => handleAdd('add-study') }}
            />
          ) : (
            <div className="space-y-3">
              {/* Instruction hint when no study is selected */}
              {!selectedNode && (
                <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-700 dark:text-blue-300">
                  <Users className="h-4 w-4 flex-shrink-0" />
                  <span>
                    <strong>Tip:</strong> Click on a study below to manage its members, add releases, or edit details. 
                    You can also click the <Users className="h-3.5 w-3.5 inline mx-0.5" /> icon next to a study name.
                  </span>
                </div>
              )}
              <div className="border rounded-lg p-4 min-h-[400px]">
                {tree.map((node) => renderTreeNode(node))}
              </div>
            </div>
          )}
          {selectedNode && (
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium uppercase",
                    selectedNode.type === 'study' && "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
                    selectedNode.type === 'release' && "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
                    selectedNode.type === 'effort' && "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300"
                  )}>
                    {selectedNode.type}
                  </span>
                  <span className="font-medium text-foreground">{selectedNode.label}</span>
                </div>
                <div className="flex items-center gap-2">
                  {selectedNode.type === 'study' && canManageMembers && (
                    <Button size="sm" variant="outline" onClick={() => setMembersDialogOpen(true)}>
                      <Users className="h-4 w-4 mr-2" />
                      Manage Members
                    </Button>
                  )}
                  {selectedNode.type === 'effort' && canEditSelectedStudy && (
                    <>
                      <Button size="sm" variant="outline" onClick={() => setUseCasesDialogOpen(true)}>
                        <Tag className="h-4 w-4 mr-2" />
                        Manage Use Cases
                      </Button>
                      {/* Lock Toggle Switch - Only show if manual lock/unlock is enabled */}
                      {showManualLockToggle && (
                        <TooltipWrapper
                          content={(selectedNode.data as ReportingEffort).is_locked 
                            ? 'Currently Locked - Click to unlock' 
                            : 'Currently Unlocked - Click to lock'}
                          side="bottom"
                        >
                          <button
                            type="button"
                            onClick={() => setLockDialogOpen(true)}
                            className="flex items-center gap-2 px-3 py-1.5 rounded-md border hover:bg-accent transition-colors"
                          >
                            <span className="text-sm font-medium text-muted-foreground">
                              {(selectedNode.data as ReportingEffort).is_locked ? 'Locked' : 'Unlocked'}
                            </span>
                            <div className="relative">
                              <div
                                className={`block h-5 w-9 rounded-full transition-colors ${
                                  (selectedNode.data as ReportingEffort).is_locked 
                                    ? 'bg-amber-500' 
                                    : 'bg-gray-300 dark:bg-gray-600'
                                }`}
                              />
                              <div
                                className={`absolute left-0.5 top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-white shadow transition-transform ${
                                  (selectedNode.data as ReportingEffort).is_locked ? 'translate-x-4' : ''
                                }`}
                              >
                                {(selectedNode.data as ReportingEffort).is_locked ? (
                                  <Lock className="h-2.5 w-2.5 text-amber-500" />
                                ) : (
                                  <Unlock className="h-2.5 w-2.5 text-gray-400" />
                                )}
                              </div>
                            </div>
                          </button>
                        </TooltipWrapper>
                      )}
                      {/* Lock Status Indicator - Show when auto-lock is enabled and effort is locked */}
                      {!showManualLockToggle && (selectedNode.data as ReportingEffort).is_locked && (
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
                          <Lock className="h-4 w-4 text-amber-500" />
                          <span className="text-sm font-medium text-amber-700 dark:text-amber-400">Locked</span>
                        </div>
                      )}
                      <Button size="sm" variant="ghost" onClick={() => setLockHistoryDialogOpen(true)}>
                        <History className="h-4 w-4 mr-2" />
                        Lock History
                      </Button>
                      {/* Sign Button - Only show if not already signed */}
                      {!(selectedNode.data as ReportingEffort).is_signed && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setSignDialogOpen(true)}
                          className="border-blue-500/50 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950"
                        >
                          <FileSignature className="h-4 w-4 mr-2" />
                          Sign
                        </Button>
                      )}
                    </>
                  )}
                </div>
              </div>
              {selectedNode.type === 'study' && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Use "Manage Members" to add team members and assign roles (Lead, Editor, Viewer) for this study.
                </p>
              )}
              {/* Signature Status Banner */}
              {selectedNode.type === 'effort' && (selectedNode.data as ReportingEffort).is_signed && (
                <div className="mt-3 p-3 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Shield className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <div className="text-sm">
                      <p className="font-medium text-green-700 dark:text-green-400">
                        Electronically Signed
                        {(selectedNode.data as ReportingEffort).signed_by_username && (
                          <span className="font-normal text-green-600 dark:text-green-500">
                            {' '}by {(selectedNode.data as ReportingEffort).signed_by_username}
                          </span>
                        )}
                        {(selectedNode.data as ReportingEffort).signed_at && (
                          <span className="font-normal text-green-600 dark:text-green-500">
                            {' '}on {new Date((selectedNode.data as ReportingEffort).signed_at!).toLocaleDateString()}
                          </span>
                        )}
                      </p>
                      {(selectedNode.data as ReportingEffort).signature_reason && (
                        <p className="text-green-600 dark:text-green-400 mt-1">
                          Reason: {(selectedNode.data as ReportingEffort).signature_reason}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
              {selectedNode.type === 'effort' && (selectedNode.data as ReportingEffort).is_locked && !(selectedNode.data as ReportingEffort).is_signed && (
                <div className="mt-3 p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Lock className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                    <div className="text-sm">
                      <p className="font-medium text-amber-700 dark:text-amber-400">
                        Locked
                        {(selectedNode.data as ReportingEffort).locked_by_username && (
                          <span className="font-normal text-amber-600 dark:text-amber-500">
                            {' '}by {(selectedNode.data as ReportingEffort).locked_by_username}
                          </span>
                        )}
                        {(selectedNode.data as ReportingEffort).locked_at && (
                          <span className="font-normal text-amber-600 dark:text-amber-500">
                            {' '}on {new Date((selectedNode.data as ReportingEffort).locked_at!).toLocaleDateString()}
                          </span>
                        )}
                      </p>
                      {(selectedNode.data as ReportingEffort).lock_reason && (
                        <p className="text-amber-600 dark:text-amber-400 mt-1">
                          {(selectedNode.data as ReportingEffort).lock_reason}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
              {selectedNode.type === 'effort' && (selectedNode.data as ReportingEffort).use_cases && (selectedNode.data as ReportingEffort).use_cases!.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {(selectedNode.data as ReportingEffort).use_cases?.map((uc: UseCaseSummary) => (
                    <span
                      key={uc.id}
                      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                      style={{ backgroundColor: `${uc.color}20`, color: uc.color }}
                    >
                      {uc.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {dialogMode === 'add-study' && 'Add New Study'}
              {dialogMode === 'add-release' && 'Add Database Release'}
              {dialogMode === 'add-effort' && 'Add Reporting Effort'}
              {dialogMode === 'edit' && `Edit ${selectedNode?.type}`}
            </DialogTitle>
            <DialogDescription>
              {dialogMode === 'add-study' && 'Create a new study in the system.'}
              {dialogMode === 'add-release' && `Add a database release to ${selectedNode?.label}.`}
              {dialogMode === 'add-effort' && `Add a reporting effort to ${selectedNode?.label}.`}
              {dialogMode === 'edit' && 'Update the selected item.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="label">Label</Label>
              <Input
                id="label"
                value={formData.label}
                onChange={(e) => setFormData((prev) => ({ ...prev, label: e.target.value }))}
                placeholder="Enter label..."
              />
            </div>
            {(dialogMode === 'add-release' || (dialogMode === 'edit' && selectedNode?.type === 'release')) && (
              <div className="grid gap-2">
                <Label htmlFor="date">Release Date</Label>
                <Input
                  id="date"
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData((prev) => ({ ...prev, date: e.target.value }))}
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!formData.label}>
              {dialogMode === 'edit' ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title={`Delete ${selectedNode?.type}?`}
        description={`Are you sure you want to delete "${selectedNode?.label}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
      />

      {/* Study Members Dialog */}
      <StudyMembersDialog
        study={selectedNode?.type === 'study' ? (selectedNode.data as Study) : null}
        open={membersDialogOpen}
        onOpenChange={setMembersDialogOpen}
      />

      <ExcelUpload
        open={bulkUploadOpen}
        onOpenChange={setBulkUploadOpen}
        title="Bulk Upload Study/Release/Effort"
        description="Upload a CSV (or Excel saved as CSV) with Study, Database_Release, Reporting_Effort columns."
        columns={[
          { key: 'study_label', label: 'Study', required: true },
          { key: 'database_release_label', label: 'Database_Release', required: true },
          { key: 'reporting_effort_label', label: 'Reporting_Effort', required: true },
        ]}
        sampleData={[
          ['STUDY_001', 'DB001_JAN2026', 'EFFORT_Q1_2026'],
          ['STUDY_001', 'DB001_JAN2026', 'EFFORT_Q2_2026'],
          ['STUDY_002', 'DB002_FEB2026', 'EFFORT_MAIN'],
        ]}
        templateFilename="study_release_effort.csv"
        onUpload={handleBulkUploadRows}
      />

      {/* Use Cases Management Dialog */}
      <Dialog open={useCasesDialogOpen} onOpenChange={setUseCasesDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Manage Use Cases</DialogTitle>
            <DialogDescription>
              Assign use cases to {selectedNode?.label}
            </DialogDescription>
          </DialogHeader>
          {(() => {
            // Get fresh effort data from the query instead of stale selectedNode.data
            const currentEffort = selectedNode?.type === 'effort'
              ? efforts.find(e => e.id === selectedNode.id)
              : null
            const assignedUseCases = currentEffort?.use_cases || []

            return (
              <div className="space-y-4 py-4">
                {/* Current assignments */}
                {selectedNode?.type === 'effort' && (
                  <div className="space-y-2">
                    <Label>Assigned Use Cases</Label>
                    {assignedUseCases.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {assignedUseCases.map((uc: UseCaseSummary) => (
                          <span
                            key={uc.id}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
                            style={{ backgroundColor: `${uc.color}20`, color: uc.color }}
                          >
                            {uc.name}
                            <button
                              onClick={() => removeUseCaseAssignment.mutate({
                                reportingEffortId: selectedNode.id,
                                useCaseId: uc.id
                              })}
                              className="hover:opacity-70"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No use cases assigned</p>
                    )}
                  </div>
                )}

                {/* Available use cases to add */}
                <div className="space-y-2">
                  <Label>Add Use Cases</Label>
                  <div className="space-y-2 max-h-48 overflow-y-auto border rounded-md p-2">
                    {allUseCases
                      .filter((uc: UseCase) =>
                        !assignedUseCases.some((assigned: UseCaseSummary) => assigned.id === uc.id)
                      )
                      .map((uc: UseCase) => (
                        <div
                          key={uc.id}
                          className="flex items-center justify-between p-2 hover:bg-accent rounded cursor-pointer"
                          onClick={() => {
                            if (selectedNode?.type === 'effort') {
                              assignUseCase.mutate({
                                reportingEffortId: selectedNode.id,
                                useCaseId: uc.id
                              })
                            }
                          }}
                        >
                          <div className="flex items-center gap-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: uc.color }}
                            />
                            <span className="text-sm">{uc.name}</span>
                          </div>
                          <Plus className="h-4 w-4 text-muted-foreground" />
                        </div>
                      ))}
                    {allUseCases.filter((uc: UseCase) =>
                      !assignedUseCases.some((assigned: UseCaseSummary) => assigned.id === uc.id)
                    ).length === 0 && (
                      <p className="text-sm text-muted-foreground text-center py-2">
                        All use cases are assigned
                      </p>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Click a use case to assign it. Manage the use case list in Settings.
                  </p>
                </div>
              </div>
            )
          })()}
          <DialogFooter>
            <Button variant="outline" onClick={() => setUseCasesDialogOpen(false)}>
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Lock/Unlock Dialog */}
      <LockReportingEffortDialog
        reportingEffort={selectedNode?.type === 'effort' ? (selectedNode.data as ReportingEffort) : null}
        open={lockDialogOpen}
        onOpenChange={setLockDialogOpen}
        onLockStatusChange={(updatedEffort) => {
          // Update the selectedNode with fresh lock status data
          if (selectedNode?.type === 'effort' && selectedNode.id === updatedEffort.id) {
            setSelectedNode({
              ...selectedNode,
              data: updatedEffort,
            })
          }
        }}
      />

      {/* Lock History Dialog */}
      <LockHistoryDialog
        reportingEffort={selectedNode?.type === 'effort' ? (selectedNode.data as ReportingEffort) : null}
        open={lockHistoryDialogOpen}
        onOpenChange={setLockHistoryDialogOpen}
      />

      {/* Sign Reporting Effort Dialog */}
      <SignReportingEffortDialog
        reportingEffort={selectedNode?.type === 'effort' ? (selectedNode.data as ReportingEffort) : null}
        open={signDialogOpen}
        onOpenChange={setSignDialogOpen}
        onSignComplete={(updatedEffort) => {
          // Update the selectedNode with fresh signature data
          if (selectedNode?.type === 'effort' && selectedNode.id === updatedEffort.id) {
            setSelectedNode({
              ...selectedNode,
              data: updatedEffort,
            })
          }
        }}
        onSetupSignature={() => {
          setSignDialogOpen(false)
          setSignatureSetupDialogOpen(true)
        }}
      />

      {/* Signature Setup Dialog */}
      <SignatureSetupDialog
        open={signatureSetupDialogOpen}
        onOpenChange={setSignatureSetupDialogOpen}
      />
    </div>
  )
}


