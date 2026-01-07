import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { phasesApi, milestonesApi } from '@/api'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import {
  Plus,
  Pencil,
  Trash2,
  ChevronDown,
  ChevronRight,
  Calendar,
  CheckCircle2,
  Target,
  Copy,
  Link2,
  AlertTriangle,
  Tag
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { format, parseISO } from 'date-fns'
import { toast } from 'sonner'
import type {
  ReportingEffortPhase,
  ReportingEffortMilestone,
  PhaseFormData,
  MilestoneFormData,
  MilestoneLinkableSubtype
} from '@/types'

// Linkable subtypes for milestone-tracker linking
const LINKABLE_SUBTYPES: MilestoneLinkableSubtype[] = ['Table', 'Listing', 'Figure', 'SDTM', 'ADaM']

interface MilestoneEditorProps {
  reportingEffortId: number
  reportingEffortLabel?: string
}

export function MilestoneEditor({ reportingEffortId, reportingEffortLabel }: MilestoneEditorProps) {
  const queryClient = useQueryClient()
  const [expandedPhases, setExpandedPhases] = useState<Set<number>>(new Set())
  
  // Dialog states
  const [phaseDialogOpen, setPhaseDialogOpen] = useState(false)
  const [milestoneDialogOpen, setMilestoneDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [copyDialogOpen, setCopyDialogOpen] = useState(false)
  
  // Current editing items
  const [editingPhase, setEditingPhase] = useState<ReportingEffortPhase | null>(null)
  const [editingMilestone, setEditingMilestone] = useState<ReportingEffortMilestone | null>(null)
  const [currentPhaseId, setCurrentPhaseId] = useState<number | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<{ type: 'phase' | 'milestone'; id: number; name: string } | null>(null)

  // Form data
  const [phaseForm, setPhaseForm] = useState<PhaseFormData>({ name: '' })
  const [milestoneForm, setMilestoneForm] = useState<MilestoneFormData>({ name: '' })
  const [copyForm, setCopyForm] = useState<{ sourceEffortId: string; dateOffset: string }>({
    sourceEffortId: '',
    dateOffset: '0',
  })

  // Fetch phases with milestones
  const { data: phases = [], isLoading } = useQuery({
    queryKey: ['phases', reportingEffortId],
    queryFn: () => phasesApi.getByReportingEffort(reportingEffortId),
  })

  // Fetch available sources for copying
  const { data: availableSources = [] } = useQuery({
    queryKey: ['milestone-sources', reportingEffortId],
    queryFn: () => milestonesApi.getAvailableSources(reportingEffortId),
  })

  // Fetch available tags for milestone linking
  const { data: availableTags = [] } = useQuery({
    queryKey: ['milestone-linking-tags'],
    queryFn: () => milestonesApi.getTagsForLinking(),
  })

  // Mutations
  const createPhaseMutation = useMutation({
    mutationFn: (data: PhaseFormData) => phasesApi.create(reportingEffortId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phases', reportingEffortId] })
      queryClient.invalidateQueries({ queryKey: ['milestones-dashboard'] })
      toast.success('Phase created successfully')
      setPhaseDialogOpen(false)
      resetPhaseForm()
    },
    onError: () => toast.error('Failed to create phase'),
  })

  const updatePhaseMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<PhaseFormData> }) =>
      phasesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phases', reportingEffortId] })
      queryClient.invalidateQueries({ queryKey: ['milestones-dashboard'] })
      toast.success('Phase updated successfully')
      setPhaseDialogOpen(false)
      resetPhaseForm()
    },
    onError: () => toast.error('Failed to update phase'),
  })

  const deletePhaseMutation = useMutation({
    mutationFn: (id: number) => phasesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phases', reportingEffortId] })
      queryClient.invalidateQueries({ queryKey: ['milestones-dashboard'] })
      toast.success('Phase deleted successfully')
      setDeleteDialogOpen(false)
      setDeleteTarget(null)
    },
    onError: () => toast.error('Failed to delete phase'),
  })

  const createMilestoneMutation = useMutation({
    mutationFn: ({ phaseId, data }: { phaseId: number; data: MilestoneFormData }) =>
      milestonesApi.create(phaseId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phases', reportingEffortId] })
      queryClient.invalidateQueries({ queryKey: ['milestones-dashboard'] })
      toast.success('Milestone created successfully')
      setMilestoneDialogOpen(false)
      resetMilestoneForm()
    },
    onError: () => toast.error('Failed to create milestone'),
  })

  const updateMilestoneMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<MilestoneFormData> }) =>
      milestonesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phases', reportingEffortId] })
      queryClient.invalidateQueries({ queryKey: ['milestones-dashboard'] })
      toast.success('Milestone updated successfully')
      setMilestoneDialogOpen(false)
      resetMilestoneForm()
    },
    onError: () => toast.error('Failed to update milestone'),
  })

  const deleteMilestoneMutation = useMutation({
    mutationFn: (id: number) => milestonesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phases', reportingEffortId] })
      queryClient.invalidateQueries({ queryKey: ['milestones-dashboard'] })
      toast.success('Milestone deleted successfully')
      setDeleteDialogOpen(false)
      setDeleteTarget(null)
    },
    onError: () => toast.error('Failed to delete milestone'),
  })

  const toggleCompleteMutation = useMutation({
    mutationFn: ({ id, isCompleted }: { id: number; isCompleted: boolean }) =>
      isCompleted ? milestonesApi.markIncomplete(id) : milestonesApi.markComplete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phases', reportingEffortId] })
      queryClient.invalidateQueries({ queryKey: ['milestones-dashboard'] })
    },
    onError: () => toast.error('Failed to update milestone status'),
  })

  const copyFromEffortMutation = useMutation({
    mutationFn: ({ sourceId, dateOffset }: { sourceId: number; dateOffset: number }) =>
      milestonesApi.copyFromEffort(reportingEffortId, sourceId, dateOffset || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['phases', reportingEffortId] })
      queryClient.invalidateQueries({ queryKey: ['milestones-dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['milestone-sources'] })
      toast.success('Milestones copied successfully')
      setCopyDialogOpen(false)
      setCopyForm({ sourceEffortId: '', dateOffset: '0' })
    },
    onError: () => toast.error('Failed to copy milestones'),
  })

  // Helpers
  const resetPhaseForm = () => {
    setPhaseForm({ name: '' })
    setEditingPhase(null)
  }

  const resetMilestoneForm = () => {
    setMilestoneForm({ name: '' })
    setEditingMilestone(null)
    setCurrentPhaseId(null)
  }

  const togglePhase = (phaseId: number) => {
    setExpandedPhases(prev => {
      const next = new Set(prev)
      if (next.has(phaseId)) {
        next.delete(phaseId)
      } else {
        next.add(phaseId)
      }
      return next
    })
  }

  const openPhaseDialog = (phase?: ReportingEffortPhase) => {
    if (phase) {
      setEditingPhase(phase)
      setPhaseForm({ name: phase.name, display_order: phase.display_order })
    } else {
      resetPhaseForm()
    }
    setPhaseDialogOpen(true)
  }

  const openMilestoneDialog = (phaseId: number, milestone?: ReportingEffortMilestone) => {
    setCurrentPhaseId(phaseId)
    if (milestone) {
      setEditingMilestone(milestone)
      setMilestoneForm({
        name: milestone.name,
        start_date: milestone.start_date,
        due_date: milestone.due_date,
        responsibility: milestone.responsibility,
        comments: milestone.comments,
        is_completed: milestone.is_completed,
        linked_subtype: milestone.linked_subtype || null,
        linked_tag_id: milestone.linked_tag_id || null,
      })
    } else {
      resetMilestoneForm()
      setCurrentPhaseId(phaseId)
    }
    setMilestoneDialogOpen(true)
  }

  const openDeleteDialog = (type: 'phase' | 'milestone', id: number, name: string) => {
    setDeleteTarget({ type, id, name })
    setDeleteDialogOpen(true)
  }

  const handlePhaseSubmit = () => {
    if (!phaseForm.name.trim()) return

    if (editingPhase) {
      updatePhaseMutation.mutate({ id: editingPhase.id, data: phaseForm })
    } else {
      createPhaseMutation.mutate(phaseForm)
    }
  }

  const handleMilestoneSubmit = () => {
    if (!milestoneForm.name.trim() || !currentPhaseId) return

    if (editingMilestone) {
      updateMilestoneMutation.mutate({ id: editingMilestone.id, data: milestoneForm })
    } else {
      createMilestoneMutation.mutate({ phaseId: currentPhaseId, data: milestoneForm })
    }
  }

  const handleDelete = () => {
    if (!deleteTarget) return

    if (deleteTarget.type === 'phase') {
      deletePhaseMutation.mutate(deleteTarget.id)
    } else {
      deleteMilestoneMutation.mutate(deleteTarget.id)
    }
  }

  if (isLoading) {
    return <PageLoader text="Loading milestones..." />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">
            Milestones {reportingEffortLabel && `- ${reportingEffortLabel}`}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {availableSources.length > 0 && (
            <Button onClick={() => setCopyDialogOpen(true)} size="sm" variant="outline">
              <Copy className="h-4 w-4 mr-1" />
              Copy from...
            </Button>
          )}
          <Button onClick={() => openPhaseDialog()} size="sm">
            <Plus className="h-4 w-4 mr-1" />
            Add Phase
          </Button>
        </div>
      </div>

      {phases.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="No milestones yet"
          description="Add phases and milestones to track key dates and deliverables for this reporting effort."
          action={{
            label: 'Add First Phase',
            onClick: () => openPhaseDialog(),
          }}
        />
      ) : (
        <div className="space-y-3">
          {phases.map((phase) => (
            <Card key={phase.id} className="overflow-hidden">
              {/* Phase Header */}
              <div
                className="flex items-center gap-3 p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => togglePhase(phase.id)}
              >
                <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0">
                  {expandedPhases.has(phase.id) ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{phase.name}</span>
                    <Badge variant="outline" className="text-xs">
                      {phase.milestones?.length || 0} milestone{(phase.milestones?.length || 0) !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                </div>
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => openMilestoneDialog(phase.id)}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => openPhaseDialog(phase)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-destructive hover:text-destructive"
                    onClick={() => openDeleteDialog('phase', phase.id, phase.name)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Milestones */}
              {expandedPhases.has(phase.id) && (
                <div className="border-t bg-muted/20">
                  {phase.milestones && phase.milestones.length > 0 ? (
                    <div className="divide-y">
                      {phase.milestones.map((milestone) => (
                        <div
                          key={milestone.id}
                          className={cn(
                            'flex items-center gap-3 p-3 pl-12',
                            milestone.is_completed && 'bg-green-50/50 dark:bg-green-950/20'
                          )}
                        >
                          <Checkbox
                            checked={milestone.is_completed}
                            onCheckedChange={() =>
                              toggleCompleteMutation.mutate({
                                id: milestone.id,
                                isCompleted: milestone.is_completed,
                              })
                            }
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span
                                className={cn(
                                  'font-medium truncate',
                                  milestone.is_completed && 'line-through text-muted-foreground'
                                )}
                              >
                                {milestone.name}
                              </span>
                              {milestone.is_completed && (
                                <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                              )}
                            </div>
                            <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1 flex-wrap">
                              {(milestone.start_date || milestone.due_date) && (
                                <div className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  {milestone.start_date && milestone.due_date ? (
                                    <span>
                                      {format(parseISO(milestone.start_date), 'MMM d')} → {format(parseISO(milestone.due_date), 'MMM d, yyyy')}
                                    </span>
                                  ) : milestone.due_date ? (
                                    <span>Due: {format(parseISO(milestone.due_date), 'MMM d, yyyy')}</span>
                                  ) : (
                                    <span>Start: {format(parseISO(milestone.start_date!), 'MMM d, yyyy')}</span>
                                  )}
                                </div>
                              )}
                              {milestone.responsibility && (
                                <span>Resp: {milestone.responsibility}</span>
                              )}
                              {/* Show linked subtype/tag */}
                              {milestone.linked_subtype && (
                                <Badge variant="secondary" className="text-[10px] h-4">
                                  <Link2 className="h-2.5 w-2.5 mr-1" />
                                  {milestone.linked_subtype}
                                </Badge>
                              )}
                              {milestone.linked_tag_id && (
                                <Badge variant="outline" className="text-[10px] h-4">
                                  <Tag className="h-2.5 w-2.5 mr-1" />
                                  Tag
                                </Badge>
                              )}
                              {milestone.comments && (
                                <span className="truncate max-w-[200px]" title={milestone.comments}>
                                  Note: {milestone.comments}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => openMilestoneDialog(phase.id, milestone)}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-destructive hover:text-destructive"
                              onClick={() => openDeleteDialog('milestone', milestone.id, milestone.name)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 text-center text-sm text-muted-foreground">
                      No milestones in this phase.{' '}
                      <Button
                        variant="link"
                        className="h-auto p-0"
                        onClick={() => openMilestoneDialog(phase.id)}
                      >
                        Add one
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}

      {/* Phase Dialog */}
      <Dialog open={phaseDialogOpen} onOpenChange={setPhaseDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingPhase ? 'Edit Phase' : 'Add Phase'}</DialogTitle>
            <DialogDescription>
              {editingPhase
                ? 'Update the phase details below.'
                : 'Create a new phase to group related milestones.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="phase-name">Phase Name</Label>
              <Input
                id="phase-name"
                placeholder="e.g., Blinded DMC/DSMT Delivery"
                value={phaseForm.name}
                onChange={(e) => setPhaseForm((prev) => ({ ...prev, name: e.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPhaseDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handlePhaseSubmit}
              disabled={!phaseForm.name.trim() || createPhaseMutation.isPending || updatePhaseMutation.isPending}
            >
              {editingPhase ? 'Save Changes' : 'Create Phase'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Milestone Dialog */}
      <Dialog open={milestoneDialogOpen} onOpenChange={setMilestoneDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingMilestone ? 'Edit Milestone' : 'Add Milestone'}</DialogTitle>
            <DialogDescription>
              {editingMilestone
                ? 'Update the milestone details below.'
                : 'Create a new milestone to track a key date or deliverable.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4 max-h-[70vh] overflow-y-auto">
            <div className="space-y-2">
              <Label htmlFor="milestone-name">Milestone Name *</Label>
              <Input
                id="milestone-name"
                placeholder="e.g., Deliver all SDTMs"
                value={milestoneForm.name}
                onChange={(e) => setMilestoneForm((prev) => ({ ...prev, name: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="milestone-start-date">Start Date</Label>
                <Input
                  id="milestone-start-date"
                  type="date"
                  value={milestoneForm.start_date || ''}
                  onChange={(e) =>
                    setMilestoneForm((prev) => ({ ...prev, start_date: e.target.value || undefined }))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="milestone-due-date">Due Date</Label>
                <Input
                  id="milestone-due-date"
                  type="date"
                  value={milestoneForm.due_date || ''}
                  onChange={(e) =>
                    setMilestoneForm((prev) => ({ ...prev, due_date: e.target.value || undefined }))
                  }
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="milestone-responsibility">Responsibility</Label>
              <Input
                id="milestone-responsibility"
                placeholder="e.g., Tigermed, Geron, PXL"
                value={milestoneForm.responsibility || ''}
                onChange={(e) =>
                  setMilestoneForm((prev) => ({
                    ...prev,
                    responsibility: e.target.value || undefined,
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="milestone-comments">Comments</Label>
              <Textarea
                id="milestone-comments"
                placeholder="Additional notes or context"
                value={milestoneForm.comments || ''}
                onChange={(e) =>
                  setMilestoneForm((prev) => ({ ...prev, comments: e.target.value || undefined }))
                }
                rows={2}
              />
            </div>

            {/* Tracker Linking Section */}
            <Separator className="my-4" />
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Link2 className="h-4 w-4 text-primary" />
                <Label className="text-sm font-medium">Link to Tracker Items</Label>
              </div>
              <p className="text-xs text-muted-foreground">
                Link this milestone to tracker items by item subtype or tag. Linked items will show
                warnings if their due dates are after the milestone due date.
              </p>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="linked-subtype" className="text-xs">Link by Subtype</Label>
                  <Select
                    value={milestoneForm.linked_subtype || 'none'}
                    onValueChange={(v) =>
                      setMilestoneForm((prev) => ({
                        ...prev,
                        linked_subtype: v === 'none' ? null : (v as MilestoneLinkableSubtype),
                      }))
                    }
                  >
                    <SelectTrigger id="linked-subtype">
                      <SelectValue placeholder="Select subtype" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">
                        <span className="text-muted-foreground">No subtype link</span>
                      </SelectItem>
                      {LINKABLE_SUBTYPES.map((subtype) => (
                        <SelectItem key={subtype} value={subtype}>
                          {subtype}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Auto-links all items of this type
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="linked-tag" className="text-xs">Link by Tag</Label>
                  <Select
                    value={milestoneForm.linked_tag_id?.toString() || 'none'}
                    onValueChange={(v) =>
                      setMilestoneForm((prev) => ({
                        ...prev,
                        linked_tag_id: v === 'none' ? null : Number(v),
                      }))
                    }
                  >
                    <SelectTrigger id="linked-tag">
                      <SelectValue placeholder="Select tag" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">
                        <span className="text-muted-foreground">No tag link</span>
                      </SelectItem>
                      {availableTags.map((tag) => (
                        <SelectItem key={tag.id} value={tag.id.toString()}>
                          <div className="flex items-center gap-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: tag.color }}
                            />
                            {tag.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Auto-links items with this tag
                  </p>
                </div>
              </div>

              {(milestoneForm.linked_subtype || milestoneForm.linked_tag_id) && (
                <div className="flex items-start gap-2 p-2 bg-blue-50 dark:bg-blue-950/30 rounded-md text-xs">
                  <Tag className="h-3.5 w-3.5 text-blue-600 mt-0.5 shrink-0" />
                  <div className="text-blue-700 dark:text-blue-300">
                    Items matching this criteria will be automatically linked.
                    {milestoneForm.linked_subtype && milestoneForm.linked_tag_id && (
                      <span className="block mt-1">
                        Both subtype ({milestoneForm.linked_subtype}) and tag links will be combined.
                      </span>
                    )}
                  </div>
                </div>
              )}

              <p className="text-xs text-muted-foreground mt-2">
                To manually assign items to this milestone, use the Edit or Bulk Assign options in the Tracker table.
              </p>
            </div>

            {editingMilestone && (
              <>
                <Separator className="my-4" />
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="milestone-completed"
                    checked={milestoneForm.is_completed}
                    onCheckedChange={(checked) =>
                      setMilestoneForm((prev) => ({ ...prev, is_completed: checked === true }))
                    }
                  />
                  <Label htmlFor="milestone-completed">Mark as completed</Label>
                </div>
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMilestoneDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleMilestoneSubmit}
              disabled={
                !milestoneForm.name.trim() ||
                createMilestoneMutation.isPending ||
                updateMilestoneMutation.isPending
              }
            >
              {editingMilestone ? 'Save Changes' : 'Create Milestone'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {deleteTarget?.type}?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteTarget?.type === 'phase' ? (
                <>
                  This will permanently delete the phase "{deleteTarget?.name}" and all its
                  milestones. This action cannot be undone.
                </>
              ) : (
                <>
                  This will permanently delete the milestone "{deleteTarget?.name}". This action
                  cannot be undone.
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Copy from Another Effort Dialog */}
      <Dialog open={copyDialogOpen} onOpenChange={setCopyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Copy Milestones from Another Effort</DialogTitle>
            <DialogDescription>
              Select a reporting effort to copy its phases and milestones. You can optionally
              adjust all due dates by a number of days.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="source-effort">Source Reporting Effort</Label>
              <Select
                value={copyForm.sourceEffortId}
                onValueChange={(v) => setCopyForm((prev) => ({ ...prev, sourceEffortId: v }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a reporting effort" />
                </SelectTrigger>
                <SelectContent>
                  {availableSources.map((source) => (
                    <SelectItem key={source.id} value={String(source.id)}>
                      <div className="flex items-center gap-2">
                        <span>{source.label}</span>
                        <Badge variant="outline" className="text-xs">
                          {source.phase_count} phase{source.phase_count !== 1 ? 's' : ''}
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="date-offset">Date Offset (days)</Label>
              <Input
                id="date-offset"
                type="number"
                placeholder="0"
                value={copyForm.dateOffset}
                onChange={(e) =>
                  setCopyForm((prev) => ({ ...prev, dateOffset: e.target.value }))
                }
              />
              <p className="text-xs text-muted-foreground">
                Shift all due dates by this many days. Use positive numbers for future dates,
                negative for past dates.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCopyDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (copyForm.sourceEffortId) {
                  copyFromEffortMutation.mutate({
                    sourceId: Number(copyForm.sourceEffortId),
                    dateOffset: Number(copyForm.dateOffset) || 0,
                  })
                }
              }}
              disabled={!copyForm.sourceEffortId || copyFromEffortMutation.isPending}
            >
              {copyFromEffortMutation.isPending ? 'Copying...' : 'Copy Milestones'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

