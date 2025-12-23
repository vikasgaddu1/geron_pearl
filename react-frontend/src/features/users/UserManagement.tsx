import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, Plus, Edit, Trash2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { usersApi } from '@/api'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { RoleBadge } from '@/components/common/StatusBadge'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { DataTable, ColumnDef } from '@/components/common/DataTable'
import { TooltipWrapper } from '@/components/common/TooltipWrapper'
import { HelpIcon } from '@/components/common/HelpIcon'
import { useWebSocketRefresh } from '@/hooks/useWebSocket'
import type { User, UserFormData } from '@/types'
import { formatDateTime } from '@/lib/utils'

const ROLES = ['ADMIN', 'EDITOR', 'VIEWER'] as const

export function UserManagement() {
  const queryClient = useQueryClient()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    role: 'VIEWER',
    department: 'Programming',
  })

  // Query
  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.getAll,
  })

  // WebSocket refresh
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['users'] })
  }, [queryClient])

  useWebSocketRefresh(['user'], refetch)

  // Mutations
  const createUser = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      toast.success('User created successfully')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: () => toast.error('Failed to create user'),
  })

  const updateUser = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UserFormData }) =>
      usersApi.update(id, data),
    onSuccess: () => {
      toast.success('User updated successfully')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: () => toast.error('Failed to update user'),
  })

  const deleteUser = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      toast.success('User deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setSelectedUser(null)
    },
    onError: () => toast.error('Failed to delete user'),
  })

  const resetForm = () => {
    setFormData({ username: '', role: 'VIEWER', department: 'Programming' })
    setSelectedUser(null)
  }

  const handleAdd = () => {
    resetForm()
    setDialogOpen(true)
  }

  const handleEdit = (user: User) => {
    setSelectedUser(user)
    setFormData({
      username: user.username,
      role: user.role,
      department: user.department || '',
    })
    setDialogOpen(true)
  }

  const handleDelete = (user: User) => {
    setSelectedUser(user)
    setDeleteDialogOpen(true)
  }

  const handleSubmit = () => {
    if (selectedUser) {
      updateUser.mutate({ id: selectedUser.id, data: formData })
    } else {
      createUser.mutate(formData)
    }
  }

  const confirmDelete = () => {
    if (selectedUser) {
      deleteUser.mutate(selectedUser.id)
      setDeleteDialogOpen(false)
    }
  }

  // Define table columns
  const columns: ColumnDef<User>[] = [
    {
      id: 'username',
      header: 'Username',
      accessorKey: 'username',
      filterType: 'text',
      helpText: 'Unique identifier for the user. Supports wildcard (*) and regex patterns for advanced searching.',
      cell: (value) => <span className="font-medium">{value}</span>,
    },
    {
      id: 'role',
      header: 'Role',
      accessorKey: 'role',
      filterType: 'select',
      filterOptions: ['ADMIN', 'EDITOR', 'VIEWER'],
      helpText: 'User permission level. ADMIN has full system access, EDITOR can modify content, and VIEWER has read-only access.',
      cell: (value) => <RoleBadge role={value as User['role']} />,
    },
    {
      id: 'department',
      header: 'Department',
      accessorKey: 'department',
      filterType: 'text',
      helpText: 'The department or team the user belongs to.',
      cell: (value) => value || '-',
    },
    {
      id: 'created_at',
      header: 'Created',
      accessorKey: 'created_at',
      filterType: 'date',
      helpText: 'Date and time when the user account was created in the system.',
      cell: (value) => formatDateTime(value),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessorKey: 'id',
      filterType: 'none',
      enableSorting: false,
      cell: (_, user) => (
        <div className="flex justify-end gap-2">
          <TooltipWrapper content="Edit user details">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleEdit(user)}
            >
              <Edit className="h-4 w-4" />
            </Button>
          </TooltipWrapper>
          <TooltipWrapper content="Delete user">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDelete(user)}
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </TooltipWrapper>
        </div>
      ),
    },
  ]

  if (isLoading) {
    return <PageLoader text="Loading users..." />
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div className="flex items-center gap-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                User Management
              </CardTitle>
              <CardDescription>
                Manage system users and their roles
              </CardDescription>
            </div>
            <HelpIcon
              title="User Management"
              content={
                <div className="space-y-2">
                  <p>Manage all users in the system with role-based access control.</p>
                  <div className="space-y-1">
                    <p className="font-semibold text-sm">User Roles:</p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li><strong>ADMIN:</strong> Full system access and configuration</li>
                      <li><strong>EDITOR:</strong> Can create and modify content</li>
                      <li><strong>VIEWER:</strong> Read-only access</li>
                    </ul>
                  </div>
                </div>
              }
            />
          </div>
          <div className="flex gap-2">
            <TooltipWrapper content="Refresh user list">
              <Button variant="outline" size="sm" onClick={refetch}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </TooltipWrapper>
            <TooltipWrapper content="Create a new user account">
              <Button size="sm" onClick={handleAdd}>
                <Plus className="h-4 w-4 mr-2" />
                Add User
              </Button>
            </TooltipWrapper>
          </div>
        </CardHeader>
        <CardContent>
          {users.length === 0 ? (
            <EmptyState
              icon={Users}
              title="No users found"
              description="Get started by adding a user."
              action={{ label: 'Add User', onClick: handleAdd }}
            />
          ) : (
            <DataTable data={users} columns={columns} />
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedUser ? 'Edit User' : 'Add New User'}</DialogTitle>
            <DialogDescription>
              {selectedUser ? 'Update user information.' : 'Create a new user account.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="username">Username</Label>
                <HelpIcon
                  content="Enter a unique username for the user. This will be used for login and identification."
                />
              </div>
              <Input
                id="username"
                value={formData.username}
                onChange={(e) => setFormData((prev) => ({ ...prev, username: e.target.value }))}
                placeholder="e.g., john.doe"
              />
            </div>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="role">Role</Label>
                <HelpIcon
                  content="Select the user's permission level. This determines what actions they can perform in the system."
                />
              </div>
              <Select
                value={formData.role}
                onValueChange={(value) => setFormData((prev) => ({ ...prev, role: value as User['role'] }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>
                <SelectContent>
                  {ROLES.map((role) => (
                    <SelectItem key={role} value={role} className="capitalize">
                      {role}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="department">Department (Optional)</Label>
                <HelpIcon
                  content="Optionally specify the user's department or team for organizational purposes."
                />
              </div>
              <Input
                id="department"
                value={formData.department}
                onChange={(e) => setFormData((prev) => ({ ...prev, department: e.target.value }))}
                placeholder="e.g., Biostatistics, Data Management"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!formData.username}>
              {selectedUser ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete User?"
        description={`Are you sure you want to delete "${selectedUser?.username}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={confirmDelete}
      />
    </div>
  )
}

