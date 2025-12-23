import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { GitBranch, Plus, Edit, Trash2, RefreshCw, ChevronRight, ChevronDown, Folder, FolderOpen, FileText } from 'lucide-react'
import { toast } from 'sonner'
import { studiesApi, databaseReleasesApi, reportingEffortsApi } from '@/api'
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
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { useWebSocketRefresh } from '@/hooks/useWebSocket'
import type { Study, DatabaseRelease, ReportingEffort } from '@/types'
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
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState<'add-study' | 'add-release' | 'add-effort' | 'edit'>('add-study')
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [formData, setFormData] = useState({ label: '', date: '' })

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
    onSuccess: () => {
      toast.success('Study updated successfully')
      queryClient.invalidateQueries({ queryKey: ['studies'] })
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

  const createEffort = useMutation({
    mutationFn: reportingEffortsApi.create,
    onSuccess: () => {
      toast.success('Reporting effort created successfully')
      queryClient.invalidateQueries({ queryKey: ['reporting-efforts'] })
      setDialogOpen(false)
    },
    onError: (error) => toast.error(`Failed to create reporting effort: ${getErrorMessage(error)}`),
  })

  // Build tree structure
  const buildTree = (): TreeNode[] => {
    return studies.map((study) => {
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
        date: release.database_release_date,
      })
    } else {
      setFormData({ label: (selectedNode.data as ReportingEffort).database_release_label, date: '' })
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
      createEffort.mutate({
        database_release_id: selectedNode.id,
        database_release_label: formData.label,
      })
    } else if (dialogMode === 'edit' && selectedNode) {
      if (selectedNode.type === 'study') {
        updateStudy.mutate({ id: selectedNode.id, data: { study_label: formData.label } })
      }
      // Add update logic for release and effort as needed
    }
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

    const Icon = node.type === 'study'
      ? (isExpanded ? FolderOpen : Folder)
      : node.type === 'release'
      ? (isExpanded ? FolderOpen : Folder)
      : FileText

    return (
      <div key={nodeKey}>
        <div
          className={cn(
            'flex items-center gap-2 py-1.5 px-2 rounded-md cursor-pointer transition-colors',
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
          <span className="text-sm">{node.label}</span>
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
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-primary" />
              Study Management
            </CardTitle>
            <CardDescription>
              Manage studies, database releases, and reporting efforts
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={refetch}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button size="sm" onClick={() => handleAdd('add-study')}>
              <Plus className="h-4 w-4 mr-2" />
              Add Study
            </Button>
            {selectedNode?.type === 'study' && (
              <Button size="sm" variant="outline" onClick={() => handleAdd('add-release')}>
                <Plus className="h-4 w-4 mr-2" />
                Add Release
              </Button>
            )}
            {selectedNode?.type === 'release' && (
              <Button size="sm" variant="outline" onClick={() => handleAdd('add-effort')}>
                <Plus className="h-4 w-4 mr-2" />
                Add Effort
              </Button>
            )}
            {selectedNode && (
              <>
                <Button size="sm" variant="secondary" onClick={handleEdit}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit
                </Button>
                <Button size="sm" variant="destructive" onClick={() => setDeleteDialogOpen(true)}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
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
            <div className="border rounded-lg p-4 min-h-[400px]">
              {tree.map((node) => renderTreeNode(node))}
            </div>
          )}
          {selectedNode && (
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">
                Selected: <span className="font-medium text-foreground capitalize">{selectedNode.type}</span> - {selectedNode.label}
              </p>
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
    </div>
  )
}


