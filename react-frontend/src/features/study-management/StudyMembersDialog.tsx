import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, UserPlus, Shield, Pencil, X, Crown, Eye, Search } from 'lucide-react'
import { toast } from 'sonner'
import { studiesApi, usersApi } from '@/api'
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
import type { Study, StudyMember, StudyRole, User } from '@/types'
import { getErrorMessage, cn } from '@/lib/utils'

const STUDY_ROLES: StudyRole[] = ['VIEWER', 'EDITOR', 'LEAD']

interface StudyMembersDialogProps {
  study: Study | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function StudyRoleBadge({ role, isExplicit }: { role: StudyRole; isExplicit: boolean }) {
  const config = {
    LEAD: { icon: Crown, className: 'bg-amber-500/15 text-amber-600 border-amber-500/30', label: 'Lead' },
    EDITOR: { icon: Pencil, className: 'bg-blue-500/15 text-blue-600 border-blue-500/30', label: 'Editor' },
    VIEWER: { icon: Eye, className: 'bg-slate-500/15 text-slate-600 border-slate-500/30', label: 'Viewer' },
  }
  
  const { icon: Icon, className, label } = config[role]
  
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

  // Fetch study members
  const { data: membersData, isLoading: membersLoading } = useQuery({
    queryKey: ['study-members', study?.id],
    queryFn: () => studiesApi.getMembers(study!.id, false), // Don't include defaults initially
    enabled: !!study && open,
  })

  // Fetch all users for the dropdown
  const { data: allUsers = [] } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.getAll,
    enabled: open,
  })

  // Mutations
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

  // Filter members by search term
  const members = membersData?.members || []
  const filteredMembers = members.filter(
    (m) =>
      m.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (m.email && m.email.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  // Get users that don't have an explicit role yet (for adding)
  const explicitMemberIds = new Set(members.filter(m => m.is_explicit_assignment).map(m => m.id))
  const availableUsers = allUsers.filter(
    (u) => 
      !explicitMemberIds.has(u.id) && 
      !u.is_admin && // Can't assign study roles to global admins
      u.is_active
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
            {/* Add Member Section */}
            <div className="border rounded-lg p-4 bg-muted/30">
              <Label className="text-sm font-medium mb-2 block">Add Member</Label>
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
                        No users available. Global admins already have LEAD access. Create non-admin users to assign study roles.
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
            <div className="flex gap-4 text-xs text-muted-foreground border-t pt-3">
              <div className="flex items-center gap-1">
                <Crown className="h-3 w-3 text-amber-600" />
                <span><strong>Lead:</strong> Full admin access within this study</span>
              </div>
              <div className="flex items-center gap-1">
                <Pencil className="h-3 w-3 text-blue-600" />
                <span><strong>Editor:</strong> Can modify assigned items</span>
              </div>
              <div className="flex items-center gap-1">
                <Eye className="h-3 w-3 text-slate-600" />
                <span><strong>Viewer:</strong> Read-only access</span>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Remove Confirmation Dialog */}
      <ConfirmDialog
        open={removeDialogOpen}
        onOpenChange={setRemoveDialogOpen}
        title="Remove Member Role?"
        description={`Remove "${memberToRemove?.username}"'s explicit role from this study? They will revert to default viewer access.`}
        confirmLabel="Remove"
        variant="destructive"
        onConfirm={handleRemoveConfirm}
      />
    </>
  )
}

