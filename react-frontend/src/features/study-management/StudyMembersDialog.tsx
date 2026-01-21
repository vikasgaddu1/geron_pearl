import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, UserPlus, Pencil, X, Crown, Search, Star, StarOff, UserCheck } from 'lucide-react'
import { toast } from 'sonner'
import { studiesApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { PageLoader } from '@/components/common/LoadingSpinner'
import type { Study, StudyMember, StudyRole, StudyResponsibleUser, StudyDefaultBiostat } from '@/types'
import { getErrorMessage, cn } from '@/lib/utils'

const STUDY_ROLES: StudyRole[] = ['EDITOR', 'BIOSTAT']

interface StudyMembersDialogProps {
  study: Study | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function StudyRoleBadge({ role, isExplicit }: { role: StudyRole; isExplicit: boolean }) {
  const config: Record<StudyRole, { icon: typeof Pencil; className: string; label: string }> = {
    EDITOR: { icon: Pencil, className: 'bg-blue-500/15 text-blue-600 border-blue-500/30', label: 'Editor' },
    BIOSTAT: { icon: UserCheck, className: 'bg-teal-500/15 text-teal-600 border-teal-500/30', label: 'Biostat' },
  }

  const { icon: Icon, className, label } = config[role] || { icon: Pencil, className: 'bg-blue-500/15 text-blue-600 border-blue-500/30', label: role }

  return (
    <Badge variant="outline" className={cn('gap-1', className, !isExplicit && 'opacity-60')}>
      <Icon className="h-3 w-3" />
      {label}
      {!isExplicit && <span className="text-[10px]">(default)</span>}
    </Badge>
  )
}

function AdminBadge({ isAdmin }: { isAdmin: boolean }) {
  return isAdmin ? (
    <Badge variant="outline" className={cn('text-[10px]', 'bg-purple-500/15 text-purple-600 border-purple-500/30')}>
      Global Admin
    </Badge>
  ) : (
    <Badge variant="outline" className={cn('text-[10px]', 'bg-gray-500/15 text-gray-600 border-gray-500/30')}>
      User
    </Badge>
  )
}

export function StudyMembersDialog({ study, open, onOpenChange }: StudyMembersDialogProps) {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [selectedRole, setSelectedRole] = useState<StudyRole>('EDITOR')
  const [editingMember, setEditingMember] = useState<StudyMember | null>(null)
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false)
  const [memberToRemove, setMemberToRemove] = useState<StudyMember | null>(null)
  // Responsible users state
  const [selectedResponsibleUserId, setSelectedResponsibleUserId] = useState<number | null>(null)
  const [removeResponsibleDialogOpen, setRemoveResponsibleDialogOpen] = useState(false)
  const [responsibleToRemove, setResponsibleToRemove] = useState<StudyResponsibleUser | null>(null)
  // Default biostat state
  const [selectedDefaultBiostatUserId, setSelectedDefaultBiostatUserId] = useState<number | null>(null)

  // Fetch study members
  const { data: membersData, isLoading: membersLoading } = useQuery({
    queryKey: ['study-members', study?.id],
    queryFn: () => studiesApi.getMembers(study!.id, false), // Don't include defaults initially
    enabled: !!study && open,
  })

  // Fetch responsible users
  const { data: responsibleData, isLoading: responsibleLoading } = useQuery({
    queryKey: ['study-responsible-users', study?.id],
    queryFn: () => studiesApi.getResponsibleUsers(study!.id),
    enabled: !!study && open,
  })

  // Fetch default biostat
  const { data: defaultBiostat, isLoading: defaultBiostatLoading } = useQuery({
    queryKey: ['study-default-biostat', study?.id],
    queryFn: () => studiesApi.getDefaultBiostat(study!.id),
    enabled: !!study && open,
  })

  // Fetch biostat users (users with BIOSTAT role for this study)
  const { data: biostatUsers = [] } = useQuery({
    queryKey: ['study-biostat-users', study?.id],
    queryFn: () => studiesApi.getBiostatUsers(study!.id),
    enabled: !!study && open,
  })

  // Fetch available users for the dropdown (non-admin, active users from the same tenant)
  const { data: allUsers = [] } = useQuery({
    queryKey: ['study-available-users', study?.id],
    queryFn: () => studiesApi.getAvailableUsers(study!.id),
    enabled: !!study && open,
  })

  // Mutations for members
  const assignMember = useMutation({
    mutationFn: ({ studyId, userId, role }: { studyId: number; userId: number; role: StudyRole }) =>
      studiesApi.assignMember(studyId, { user_id: userId, role }),
    onSuccess: () => {
      toast.success('Member role assigned successfully')
      queryClient.invalidateQueries({ queryKey: ['study-members', study?.id] })
      setSelectedUserId(null)
      setSelectedRole('EDITOR')
    },
    onError: (error) => toast.error(`Failed to assign member: ${getErrorMessage(error)}`),
  })

  const updateMemberRole = useMutation({
    mutationFn: ({ studyId, userId, role }: { studyId: number; userId: number; role: StudyRole }) =>
      studiesApi.updateMemberRole(studyId, userId, role),
    onSuccess: () => {
      toast.success('Member role updated successfully')
      queryClient.invalidateQueries({ queryKey: ['study-members', study?.id] })
      setEditingMember(null)
    },
    onError: (error) => toast.error(`Failed to update member role: ${getErrorMessage(error)}`),
  })

  const removeMember = useMutation({
    mutationFn: ({ studyId, userId }: { studyId: number; userId: number }) =>
      studiesApi.removeMember(studyId, userId),
    onSuccess: () => {
      toast.success('Member role removed - user now has default viewer access')
      queryClient.invalidateQueries({ queryKey: ['study-members', study?.id] })
      setRemoveDialogOpen(false)
      setMemberToRemove(null)
    },
    onError: (error) => toast.error(`Failed to remove member: ${getErrorMessage(error)}`),
  })

  // Mutations for responsible users
  const assignResponsibleUser = useMutation({
    mutationFn: ({ studyId, userId, isPrimary }: { studyId: number; userId: number; isPrimary: boolean }) =>
      studiesApi.assignResponsibleUser(studyId, { user_id: userId, is_primary: isPrimary }),
    onSuccess: () => {
      toast.success('Responsible user assigned successfully')
      queryClient.invalidateQueries({ queryKey: ['study-responsible-users', study?.id] })
      queryClient.invalidateQueries({ queryKey: ['me', 'study-roles'] })
      setSelectedResponsibleUserId(null)
    },
    onError: (error) => toast.error(`Failed to assign responsible user: ${getErrorMessage(error)}`),
  })

  const updateResponsibleUser = useMutation({
    mutationFn: ({ studyId, userId, isPrimary }: { studyId: number; userId: number; isPrimary: boolean }) =>
      studiesApi.updateResponsibleUser(studyId, userId, { is_primary: isPrimary }),
    onSuccess: () => {
      toast.success('Responsible user updated successfully')
      queryClient.invalidateQueries({ queryKey: ['study-responsible-users', study?.id] })
    },
    onError: (error) => toast.error(`Failed to update responsible user: ${getErrorMessage(error)}`),
  })

  const removeResponsibleUser = useMutation({
    mutationFn: ({ studyId, userId }: { studyId: number; userId: number }) =>
      studiesApi.removeResponsibleUser(studyId, userId),
    onSuccess: () => {
      toast.success('Responsible user removed')
      queryClient.invalidateQueries({ queryKey: ['study-responsible-users', study?.id] })
      queryClient.invalidateQueries({ queryKey: ['me', 'study-roles'] })
      setRemoveResponsibleDialogOpen(false)
      setResponsibleToRemove(null)
    },
    onError: (error) => toast.error(`Failed to remove responsible user: ${getErrorMessage(error)}`),
  })

  // Mutations for default biostat
  const setDefaultBiostat = useMutation({
    mutationFn: ({ studyId, userId }: { studyId: number; userId: number }) =>
      studiesApi.setDefaultBiostat(studyId, userId),
    onSuccess: () => {
      toast.success('Default biostat updated')
      queryClient.invalidateQueries({ queryKey: ['study-default-biostat', study?.id] })
      setSelectedDefaultBiostatUserId(null)
    },
    onError: (error) => toast.error(`Failed to set default biostat: ${getErrorMessage(error)}`),
  })

  const removeDefaultBiostat = useMutation({
    mutationFn: ({ studyId }: { studyId: number }) =>
      studiesApi.removeDefaultBiostat(studyId),
    onSuccess: () => {
      toast.success('Default biostat removed')
      queryClient.invalidateQueries({ queryKey: ['study-default-biostat', study?.id] })
    },
    onError: (error) => toast.error(`Failed to remove default biostat: ${getErrorMessage(error)}`),
  })

  // Filter members by search term
  const members = membersData?.members || []
  const filteredMembers = members.filter(
    (m) =>
      m.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (m.email && m.email.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  // Get responsible users
  const responsibleUsers = responsibleData?.responsible_users || []

  // Get users that don't have an explicit role yet (for adding)
  const explicitMemberIds = new Set(members.filter(m => m.is_explicit_assignment).map(m => m.id))
  const responsibleUserIds = new Set(responsibleUsers.map(r => r.user_id))
  // Filter out users who already have explicit roles (API already filters out admins and inactive users)
  const availableUsers = allUsers.filter(
    (u) => !explicitMemberIds.has(u.id)
  )

  // Users available for responsible assignment (API already filters out admins and inactive users)
  const availableResponsibleUsers = allUsers.filter(
    (u) => !responsibleUserIds.has(u.id)
  )

  const handleAssign = () => {
    if (!study || !selectedUserId) return
    assignMember.mutate({ studyId: study.id, userId: selectedUserId, role: selectedRole })
  }

  const handleUpdateRole = (member: StudyMember, newRole: StudyRole) => {
    if (!study) return
    updateMemberRole.mutate({ studyId: study.id, userId: member.id, role: newRole })
  }

  const handleRemoveClick = (member: StudyMember) => {
    setMemberToRemove(member)
    setRemoveDialogOpen(true)
  }

  const handleRemoveConfirm = () => {
    if (!study || !memberToRemove) return
    removeMember.mutate({ studyId: study.id, userId: memberToRemove.id })
  }

  // Responsible user handlers
  const handleAssignResponsible = () => {
    if (!study || !selectedResponsibleUserId) return
    // If no responsible users yet, make this one primary
    const isPrimary = responsibleUsers.length === 0
    assignResponsibleUser.mutate({ studyId: study.id, userId: selectedResponsibleUserId, isPrimary })
  }

  const handleSetPrimary = (user: StudyResponsibleUser) => {
    if (!study) return
    updateResponsibleUser.mutate({ studyId: study.id, userId: user.user_id, isPrimary: true })
  }

  const handleRemoveResponsibleClick = (user: StudyResponsibleUser) => {
    setResponsibleToRemove(user)
    setRemoveResponsibleDialogOpen(true)
  }

  const handleRemoveResponsibleConfirm = () => {
    if (!study || !responsibleToRemove) return
    removeResponsibleUser.mutate({ studyId: study.id, userId: responsibleToRemove.user_id })
  }

  // Default biostat handlers
  const handleSetDefaultBiostat = () => {
    if (!study || !selectedDefaultBiostatUserId) return
    setDefaultBiostat.mutate({ studyId: study.id, userId: selectedDefaultBiostatUserId })
  }

  const handleRemoveDefaultBiostat = () => {
    if (!study) return
    removeDefaultBiostat.mutate({ studyId: study.id })
  }

  if (!study) return null

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              Manage Study Members
            </DialogTitle>
            <DialogDescription>
              Assign roles to users for study: <strong>{study.study_label}</strong>
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-hidden flex flex-col gap-4">
            {/* Responsible Users Section */}
            <div className="border rounded-lg p-4 bg-amber-500/5 border-amber-500/20">
              <div className="flex items-center gap-2 mb-3">
                <Crown className="h-4 w-4 text-amber-600" />
                <Label className="text-sm font-medium">Responsible Users</Label>
                <span className="text-xs text-muted-foreground">(Full admin access within this study)</span>
              </div>

              {/* Current responsible users */}
              {responsibleLoading ? (
                <div className="text-sm text-muted-foreground">Loading...</div>
              ) : responsibleUsers.length === 0 ? (
                <div className="text-sm text-muted-foreground mb-3">No responsible users assigned yet.</div>
              ) : (
                <div className="flex flex-wrap gap-2 mb-3">
                  {responsibleUsers.map((user) => (
                    <Badge
                      key={user.user_id}
                      variant="outline"
                      className="gap-1.5 py-1 px-2 bg-amber-500/15 text-amber-700 border-amber-500/30"
                    >
                      {user.is_primary && <Star className="h-3 w-3 fill-current" />}
                      {user.username}
                      {user.email && <span className="text-xs opacity-70">({user.email})</span>}
                      <div className="flex items-center gap-0.5 ml-1">
                        {!user.is_primary && (
                          <button
                            onClick={() => handleSetPrimary(user)}
                            className="hover:text-amber-800 p-0.5"
                            title="Set as primary"
                          >
                            <StarOff className="h-3 w-3" />
                          </button>
                        )}
                        <button
                          onClick={() => handleRemoveResponsibleClick(user)}
                          className="hover:text-destructive p-0.5"
                          title="Remove"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    </Badge>
                  ))}
                </div>
              )}

              {/* Add responsible user */}
              <div className="flex gap-2">
                <Select
                  value={selectedResponsibleUserId?.toString() || ''}
                  onValueChange={(value) => setSelectedResponsibleUserId(parseInt(value))}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Add a responsible user..." />
                  </SelectTrigger>
                  <SelectContent>
                    {availableResponsibleUsers.length === 0 ? (
                      <div className="p-2 text-sm text-muted-foreground text-center max-w-xs">
                        No users available to assign as responsible. All users are either already responsible or are admins.
                      </div>
                    ) : (
                      availableResponsibleUsers.map((user) => (
                        <SelectItem key={user.id} value={user.id.toString()}>
                          <div className="flex items-center gap-2">
                            <span>{user.username}</span>
                            {user.email && (
                              <span className="text-xs text-muted-foreground">({user.email})</span>
                            )}
                          </div>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                <Button
                  onClick={handleAssignResponsible}
                  disabled={!selectedResponsibleUserId || assignResponsibleUser.isPending}
                  variant="outline"
                  className="border-amber-500/30 hover:bg-amber-500/10"
                >
                  <UserPlus className="h-4 w-4 mr-1" />
                  Add
                </Button>
              </div>
            </div>

            {/* Default Biostat Section */}
            <div className="border rounded-lg p-4 bg-teal-500/5 border-teal-500/20">
              <div className="flex items-center gap-2 mb-3">
                <UserCheck className="h-4 w-4 text-teal-600" />
                <Label className="text-sm font-medium">Default Biostat Reviewer</Label>
                <span className="text-xs text-muted-foreground">(Auto-assigned to TLF items after QC completion)</span>
              </div>

              {/* Current default biostat */}
              {defaultBiostatLoading ? (
                <div className="text-sm text-muted-foreground">Loading...</div>
              ) : defaultBiostat ? (
                <div className="flex items-center gap-2 mb-3">
                  <Badge
                    variant="outline"
                    className="gap-1.5 py-1 px-2 bg-teal-500/15 text-teal-700 border-teal-500/30"
                  >
                    <UserCheck className="h-3 w-3" />
                    {defaultBiostat.user_name || `User #${defaultBiostat.user_id}`}
                    {defaultBiostat.user_email && (
                      <span className="text-xs opacity-70">({defaultBiostat.user_email})</span>
                    )}
                    <button
                      onClick={handleRemoveDefaultBiostat}
                      className="hover:text-destructive p-0.5 ml-1"
                      title="Remove default biostat"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground mb-3">
                  No default biostat assigned. Assign users the BIOSTAT role below, then select one as default.
                </div>
              )}

              {/* Set default biostat */}
              <div className="flex gap-2">
                <Select
                  value={selectedDefaultBiostatUserId?.toString() || ''}
                  onValueChange={(value) => setSelectedDefaultBiostatUserId(parseInt(value))}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Select a biostat reviewer..." />
                  </SelectTrigger>
                  <SelectContent>
                    {biostatUsers.length === 0 ? (
                      <div className="p-2 text-sm text-muted-foreground text-center max-w-xs">
                        No users with BIOSTAT role. Add users with the BIOSTAT role below first.
                      </div>
                    ) : (
                      biostatUsers.map((user) => (
                        <SelectItem key={user.user_id} value={user.user_id.toString()}>
                          <div className="flex items-center gap-2">
                            <span>{user.username}</span>
                            {user.email && (
                              <span className="text-xs text-muted-foreground">({user.email})</span>
                            )}
                          </div>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                <Button
                  onClick={handleSetDefaultBiostat}
                  disabled={!selectedDefaultBiostatUserId || setDefaultBiostat.isPending}
                  variant="outline"
                  className="border-teal-500/30 hover:bg-teal-500/10"
                >
                  <UserCheck className="h-4 w-4 mr-1" />
                  Set
                </Button>
              </div>
            </div>

            {/* Add Member Section */}
            <div className="border rounded-lg p-4 bg-muted/30">
              <Label className="text-sm font-medium mb-2 block">Add Study Member</Label>
              <div className="flex gap-2">
                <Select
                  value={selectedUserId?.toString() || ''}
                  onValueChange={(value) => setSelectedUserId(parseInt(value))}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Select a user to add..." />
                  </SelectTrigger>
                  <SelectContent>
                    {availableUsers.length === 0 ? (
                      <div className="p-2 text-sm text-muted-foreground text-center max-w-xs">
                        No users available. All users already have roles assigned, or create non-admin users to assign study roles.
                      </div>
                    ) : (
                      availableUsers.map((user) => (
                        <SelectItem key={user.id} value={user.id.toString()}>
                          <div className="flex items-center gap-2">
                            <span>{user.username}</span>
                            {user.email && (
                              <span className="text-xs text-muted-foreground">({user.email})</span>
                            )}
                          </div>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>

                <Select value={selectedRole} onValueChange={(value) => setSelectedRole(value as StudyRole)}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STUDY_ROLES.map((role) => (
                      <SelectItem key={role} value={role}>
                        {role}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Button
                  onClick={handleAssign}
                  disabled={!selectedUserId || assignMember.isPending}
                >
                  <UserPlus className="h-4 w-4 mr-1" />
                  Add
                </Button>
              </div>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search members..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Members Table */}
            <ScrollArea className="flex-1 border rounded-lg">
              {membersLoading ? (
                <div className="p-8">
                  <PageLoader text="Loading members..." />
                </div>
              ) : filteredMembers.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  {searchTerm ? 'No members match your search.' : 'No members with explicit roles yet.'}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>User</TableHead>
                      <TableHead>Study Role</TableHead>
                      <TableHead>Global Role</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredMembers.map((member) => (
                      <TableRow key={member.id}>
                        <TableCell>
                          <div className="flex flex-col">
                            <span className="font-medium">{member.username}</span>
                            {member.email && (
                              <span className="text-xs text-muted-foreground">{member.email}</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          {editingMember?.id === member.id ? (
                            <Select
                              value={editingMember.role}
                              onValueChange={(value) => handleUpdateRole(member, value as StudyRole)}
                            >
                              <SelectTrigger className="w-28 h-8">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {STUDY_ROLES.map((role) => (
                                  <SelectItem key={role} value={role}>
                                    {role}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          ) : (
                            <StudyRoleBadge role={member.role} isExplicit={member.is_explicit_assignment} />
                          )}
                        </TableCell>
                        <TableCell>
                          <AdminBadge isAdmin={member.is_admin} />
                        </TableCell>
                        <TableCell className="text-right">
                          {member.is_explicit_assignment && !member.is_admin ? (
                            <div className="flex justify-end gap-1">
                              {editingMember?.id === member.id ? (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setEditingMember(null)}
                                >
                                  <X className="h-4 w-4" />
                                </Button>
                              ) : (
                                <>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setEditingMember(member)}
                                  >
                                    <Pencil className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="text-destructive hover:text-destructive"
                                    onClick={() => handleRemoveClick(member)}
                                  >
                                    <X className="h-4 w-4" />
                                  </Button>
                                </>
                              )}
                            </div>
                          ) : (
                            <span className="text-xs text-muted-foreground">
                              {member.is_admin ? 'Admin (auto)' : 'Default access'}
                            </span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </ScrollArea>

            {/* Legend */}
            <div className="flex flex-wrap gap-4 text-xs text-muted-foreground border-t pt-3">
              <div className="flex items-center gap-1">
                <Crown className="h-3 w-3 text-amber-600" />
                <span><strong>Responsible:</strong> Full admin access</span>
              </div>
              <div className="flex items-center gap-1">
                <Pencil className="h-3 w-3 text-blue-600" />
                <span><strong>Editor:</strong> Can modify items</span>
              </div>
              <div className="flex items-center gap-1">
                <UserCheck className="h-3 w-3 text-teal-600" />
                <span><strong>Biostat:</strong> Biostat reviewer</span>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Remove Member Confirmation Dialog */}
      <ConfirmDialog
        open={removeDialogOpen}
        onOpenChange={setRemoveDialogOpen}
        title="Remove Member Role?"
        description={`Remove "${memberToRemove?.username}"'s role from this study?`}
        confirmLabel="Remove"
        variant="destructive"
        onConfirm={handleRemoveConfirm}
      />

      {/* Remove Responsible User Confirmation Dialog */}
      <ConfirmDialog
        open={removeResponsibleDialogOpen}
        onOpenChange={setRemoveResponsibleDialogOpen}
        title="Remove Responsible User?"
        description={`Remove "${responsibleToRemove?.username}" as a responsible user for this study? They will lose admin access to this study.`}
        confirmLabel="Remove"
        variant="destructive"
        onConfirm={handleRemoveResponsibleConfirm}
      />
    </>
  )
}

