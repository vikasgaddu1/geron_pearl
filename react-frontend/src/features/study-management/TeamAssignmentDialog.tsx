/**
 * Team Assignment Dialog
 * 
 * Allows managing team member allocations for a study:
 * - View current team members
 * - Add new team members
 * - Change allocation percentage
 * - End assignments (with reason tracking)
 * - View allocation history
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Users, Plus, Settings, History, AlertTriangle } from 'lucide-react'
import {
  getStudyTeam,
  addTeamMember,
  changeAllocation,
  endAssignment,
  getAllocationHistory,
} from '@/api/endpoints/teamAssignments'
import { getUsers } from '@/api/endpoints/users'
import type {
  TeamMemberSummary,
  JobType,
  ExperienceLevel,
  DepartureReason,
} from '@/types/teamAssignment'

// Validation schemas
const addMemberSchema = z.object({
  user_id: z.number().min(1, 'Please select a user'),
  job_type: z.enum(['LEAD', 'PRODUCTION_PROGRAMMER', 'QC_PROGRAMMER']),
  allocation_percentage: z.number().min(1).max(100),
  productive_time_factor: z.number().min(1).max(100).default(75),
  experience_level: z.enum(['JUNIOR', 'MID', 'SENIOR']),
  effective_start_date: z.string().min(1),
  notes: z.string().optional(),
})

const changeAllocationSchema = z.object({
  new_allocation_percentage: z.number().min(1).max(100),
  new_productive_time_factor: z.number().min(1).max(100).optional(),
  new_experience_level: z.enum(['JUNIOR', 'MID', 'SENIOR']).optional(),
  new_job_type: z.enum(['LEAD', 'PRODUCTION_PROGRAMMER', 'QC_PROGRAMMER']).optional(),
  notes: z.string().optional(),
})

const endAssignmentSchema = z.object({
  departure_reason: z.enum(['left_organization', 'reassigned_fully', 'allocation_changed', 'project_ended']),
  notes: z.string().optional(),
})

type AddMemberForm = z.infer<typeof addMemberSchema>
type ChangeAllocationForm = z.infer<typeof changeAllocationSchema>
type EndAssignmentForm = z.infer<typeof endAssignmentSchema>

interface TeamAssignmentDialogProps {
  studyId: number
  studyLabel: string
  trigger?: React.ReactNode
}

export function TeamAssignmentDialog({ studyId, studyLabel, trigger }: TeamAssignmentDialogProps) {
  const [open, setOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('current')
  const [selectedMember, setSelectedMember] = useState<TeamMemberSummary | null>(null)
  const [showChangeAllocation, setShowChangeAllocation] = useState(false)
  const [showEndAssignment, setShowEndAssignment] = useState(false)
  
  const queryClient = useQueryClient()

  // Fetch team data
  const { data: teamData, isLoading: isLoadingTeam } = useQuery({
    queryKey: ['studyTeam', studyId],
    queryFn: () => getStudyTeam(studyId),
    enabled: open,
  })

  // Fetch available users
  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
    enabled: open && activeTab === 'add',
  })

  // Add member mutation
  const addMemberMutation = useMutation({
    mutationFn: (data: AddMemberForm) => addTeamMember(studyId, {
      ...data,
      productive_time_factor: data.productive_time_factor || 75,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studyTeam', studyId] })
      setActiveTab('current')
    },
  })

  // Change allocation mutation
  const changeAllocationMutation = useMutation({
    mutationFn: ({ assignmentId, data }: { assignmentId: number; data: ChangeAllocationForm }) =>
      changeAllocation(assignmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studyTeam', studyId] })
      setShowChangeAllocation(false)
      setSelectedMember(null)
    },
  })

  // End assignment mutation
  const endAssignmentMutation = useMutation({
    mutationFn: ({ assignmentId, data }: { assignmentId: number; data: EndAssignmentForm }) =>
      endAssignment(assignmentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studyTeam', studyId] })
      setShowEndAssignment(false)
      setSelectedMember(null)
    },
  })

  // Form for adding members
  const addForm = useForm<AddMemberForm>({
    resolver: zodResolver(addMemberSchema),
    defaultValues: {
      allocation_percentage: 100,
      productive_time_factor: 75,
      experience_level: 'MID',
      job_type: 'PRODUCTION_PROGRAMMER',
      effective_start_date: new Date().toISOString().split('T')[0],
    },
  })

  // Form for changing allocation
  const changeForm = useForm<ChangeAllocationForm>({
    resolver: zodResolver(changeAllocationSchema),
  })

  // Form for ending assignment
  const endForm = useForm<EndAssignmentForm>({
    resolver: zodResolver(endAssignmentSchema),
  })

  const handleAddMember = (data: AddMemberForm) => {
    addMemberMutation.mutate(data)
  }

  const handleChangeAllocation = (data: ChangeAllocationForm) => {
    if (selectedMember) {
      changeAllocationMutation.mutate({
        assignmentId: selectedMember.assignment_id,
        data,
      })
    }
  }

  const handleEndAssignment = (data: EndAssignmentForm) => {
    if (selectedMember) {
      endAssignmentMutation.mutate({
        assignmentId: selectedMember.assignment_id,
        data,
      })
    }
  }

  const getJobTypeBadge = (jobType: JobType) => {
    const styles = {
      LEAD: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      PRODUCTION_PROGRAMMER: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      QC_PROGRAMMER: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    }
    const labels = {
      LEAD: 'Lead',
      PRODUCTION_PROGRAMMER: 'Production',
      QC_PROGRAMMER: 'QC',
    }
    return <Badge className={styles[jobType]}>{labels[jobType]}</Badge>
  }

  const getExperienceBadge = (level: ExperienceLevel) => {
    const styles = {
      JUNIOR: 'bg-yellow-100 text-yellow-800',
      MID: 'bg-gray-100 text-gray-800',
      SENIOR: 'bg-indigo-100 text-indigo-800',
    }
    return <Badge variant="outline" className={styles[level]}>{level}</Badge>
  }

  // Filter out users already on the team
  const availableUsers = users?.filter(
    (user) => !teamData?.active_members.some((m) => m.user_id === user.id)
  ) || []

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Manage Team
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Team Management - {studyLabel}
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="current" className="flex items-center gap-1.5">
              <Users className="h-4 w-4" />
              Current Team ({teamData?.member_count || 0})
            </TabsTrigger>
            <TabsTrigger value="add" className="flex items-center gap-1.5">
              <Plus className="h-4 w-4" />
              Add Member
            </TabsTrigger>
          </TabsList>

          {/* Current Team Tab */}
          <TabsContent value="current" className="space-y-4">
            {/* Summary */}
            {teamData && (
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-4">
                    <div className="text-2xl font-bold text-indigo-600">
                      {teamData.member_count}
                    </div>
                    <div className="text-sm text-gray-500">Team Members</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <div className="text-2xl font-bold text-indigo-600">
                      {teamData.total_allocation_percentage}%
                    </div>
                    <div className="text-sm text-gray-500">Total Allocation</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <div className="text-2xl font-bold text-emerald-600">
                      {teamData.total_weekly_capacity_hours.toFixed(1)}h
                    </div>
                    <div className="text-sm text-gray-500">Weekly Capacity</div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Team Table */}
            {isLoadingTeam ? (
              <div className="h-40 flex items-center justify-center text-gray-500">
                Loading team...
              </div>
            ) : teamData?.active_members.length === 0 ? (
              <div className="h-40 flex flex-col items-center justify-center text-gray-500">
                <Users className="h-12 w-12 mb-2 opacity-30" />
                <p>No team members assigned</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => setActiveTab('add')}
                >
                  Add First Member
                </Button>
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Experience</TableHead>
                      <TableHead className="text-center">Allocation</TableHead>
                      <TableHead className="text-center">Effective Hours/Wk</TableHead>
                      <TableHead>Start Date</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {teamData?.active_members.map((member) => (
                      <TableRow key={member.assignment_id}>
                        <TableCell className="font-medium">{member.username}</TableCell>
                        <TableCell>{getJobTypeBadge(member.job_type)}</TableCell>
                        <TableCell>{getExperienceBadge(member.experience_level)}</TableCell>
                        <TableCell className="text-center font-mono">
                          {member.allocation_percentage}%
                        </TableCell>
                        <TableCell className="text-center font-mono">
                          {member.effective_weekly_hours.toFixed(1)}
                        </TableCell>
                        <TableCell>{member.effective_start_date}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedMember(member)
                                changeForm.reset({
                                  new_allocation_percentage: member.allocation_percentage,
                                  new_productive_time_factor: member.productive_time_factor,
                                  new_experience_level: member.experience_level,
                                  new_job_type: member.job_type,
                                })
                                setShowChangeAllocation(true)
                              }}
                            >
                              <Settings className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-600 hover:text-red-700"
                              onClick={() => {
                                setSelectedMember(member)
                                setShowEndAssignment(true)
                              }}
                            >
                              <AlertTriangle className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </TabsContent>

          {/* Add Member Tab */}
          <TabsContent value="add">
            <form onSubmit={addForm.handleSubmit(handleAddMember)} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>User *</Label>
                  <Select
                    value={addForm.watch('user_id')?.toString() || ''}
                    onValueChange={(v) => addForm.setValue('user_id', parseInt(v))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select user" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableUsers.map((user) => (
                        <SelectItem key={user.id} value={user.id.toString()}>
                          {user.username} ({user.email})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {addForm.formState.errors.user_id && (
                    <p className="text-sm text-red-500">{addForm.formState.errors.user_id.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label>Role *</Label>
                  <Select
                    value={addForm.watch('job_type')}
                    onValueChange={(v) => addForm.setValue('job_type', v as JobType)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="LEAD">Lead</SelectItem>
                      <SelectItem value="PRODUCTION_PROGRAMMER">Production Programmer</SelectItem>
                      <SelectItem value="QC_PROGRAMMER">QC Programmer</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Experience Level *</Label>
                  <Select
                    value={addForm.watch('experience_level')}
                    onValueChange={(v) => addForm.setValue('experience_level', v as ExperienceLevel)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="JUNIOR">Junior (1.5x effort)</SelectItem>
                      <SelectItem value="MID">Mid (baseline)</SelectItem>
                      <SelectItem value="SENIOR">Senior (0.75x effort)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Allocation % *</Label>
                  <Input
                    type="number"
                    min="1"
                    max="100"
                    {...addForm.register('allocation_percentage', { valueAsNumber: true })}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Productive Time % (default 75)</Label>
                  <Input
                    type="number"
                    min="1"
                    max="100"
                    {...addForm.register('productive_time_factor', { valueAsNumber: true })}
                  />
                  <p className="text-xs text-gray-500">
                    Accounts for meetings, admin work, etc.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Start Date *</Label>
                  <Input type="date" {...addForm.register('effective_start_date')} />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea {...addForm.register('notes')} placeholder="Optional notes..." />
              </div>

              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setActiveTab('current')}>
                  Cancel
                </Button>
                <Button type="submit" disabled={addMemberMutation.isPending}>
                  {addMemberMutation.isPending ? 'Adding...' : 'Add Team Member'}
                </Button>
              </div>
            </form>
          </TabsContent>
        </Tabs>

        {/* Change Allocation Dialog */}
        {showChangeAllocation && selectedMember && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md">
              <CardHeader>
                <CardTitle>Change Allocation - {selectedMember.username}</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={changeForm.handleSubmit(handleChangeAllocation)} className="space-y-4">
                  <div className="space-y-2">
                    <Label>New Allocation %</Label>
                    <Input
                      type="number"
                      min="1"
                      max="100"
                      {...changeForm.register('new_allocation_percentage', { valueAsNumber: true })}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Experience Level</Label>
                    <Select
                      value={changeForm.watch('new_experience_level')}
                      onValueChange={(v) => changeForm.setValue('new_experience_level', v as ExperienceLevel)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="JUNIOR">Junior</SelectItem>
                        <SelectItem value="MID">Mid</SelectItem>
                        <SelectItem value="SENIOR">Senior</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Notes</Label>
                    <Textarea {...changeForm.register('notes')} placeholder="Reason for change..." />
                  </div>

                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setShowChangeAllocation(false)
                        setSelectedMember(null)
                      }}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={changeAllocationMutation.isPending}>
                      {changeAllocationMutation.isPending ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}

        {/* End Assignment Dialog */}
        {showEndAssignment && selectedMember && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md">
              <CardHeader>
                <CardTitle className="text-red-600 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  End Assignment - {selectedMember.username}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={endForm.handleSubmit(handleEndAssignment)} className="space-y-4">
                  <p className="text-sm text-gray-600">
                    This will end the assignment for {selectedMember.username}. 
                    Any items assigned to them will remain assigned but will be flagged for reassignment.
                  </p>

                  <div className="space-y-2">
                    <Label>Reason *</Label>
                    <Select
                      value={endForm.watch('departure_reason')}
                      onValueChange={(v) => endForm.setValue('departure_reason', v as DepartureReason)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select reason" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="left_organization">Left Organization</SelectItem>
                        <SelectItem value="reassigned_fully">Reassigned to Another Study</SelectItem>
                        <SelectItem value="project_ended">Project Ended</SelectItem>
                        <SelectItem value="allocation_changed">Allocation Changed</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Notes</Label>
                    <Textarea {...endForm.register('notes')} placeholder="Additional details..." />
                  </div>

                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setShowEndAssignment(false)
                        setSelectedMember(null)
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant="destructive"
                      disabled={endAssignmentMutation.isPending}
                    >
                      {endAssignmentMutation.isPending ? 'Ending...' : 'End Assignment'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

