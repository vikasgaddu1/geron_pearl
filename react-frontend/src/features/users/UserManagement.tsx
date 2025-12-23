import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users, Plus, Edit, Trash2, RefreshCw, Eye, EyeOff } from 'lucide-react'
import { toast } from 'sonner'
import { usersApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
import { formatDateTime, getErrorMessage, generateSecurePassword, isValidEmail } from '@/lib/utils'

const ROLES = ['ADMIN', 'EDITOR', 'VIEWER'] as const

export function UserManagement() {
  const queryClient = useQueryClient()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [generatedPassword, setGeneratedPassword] = useState<string | null>(null)
  const [emailError, setEmailError] = useState<string | null>(null)
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    email: '',
    password: '',
    role: 'VIEWER',
    department: 'Programming',
    generatePassword: false,
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
      if (generatedPassword) {
        toast.success(
          <div className="space-y-2">
            <div>User created successfully</div>
            <div className="font-mono text-sm bg-muted p-2 rounded border">
              <div className="font-semibold mb-1">Generated Password:</div>
              <div className="break-all">{generatedPassword}</div>
            </div>
            <div className="text-xs text-muted-foreground">
              Please share this password with the user securely.
            </div>
          </div>,
          { duration: 10000 }
        )
        setGeneratedPassword(null)
      } else {
        toast.success('User created successfully')
      }
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error) => toast.error(`Failed to create user: ${getErrorMessage(error)}`),
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
    onError: (error) => toast.error(`Failed to update user: ${getErrorMessage(error)}`),
  })

  const deleteUser = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      toast.success('User deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setSelectedUser(null)
    },
    onError: (error) => toast.error(`Failed to delete user: ${getErrorMessage(error)}`),
  })

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      password: '',
      role: 'VIEWER',
      department: 'Programming',
      generatePassword: false,
    })
    setSelectedUser(null)
    setShowPassword(false)
    setGeneratedPassword(null)
    setEmailError(null)
  }

  const handleAdd = () => {
    resetForm()
    setDialogOpen(true)
  }

  const handleEdit = (user: User) => {
    setSelectedUser(user)
    setFormData({
      username: user.username,
      email: user.email || '',
      password: '', // Don't populate password for editing
      role: user.role,
      department: user.department || '',
      generatePassword: false,
    })
    setShowPassword(false)
    setGeneratedPassword(null)
    setEmailError(null)
    setDialogOpen(true)
  }

  const handleDelete = (user: User) => {
    setSelectedUser(user)
    setDeleteDialogOpen(true)
  }

  const handleEmailChange = (value: string) => {
    setFormData((prev) => ({ ...prev, email: value }))
    // Validate email format
    if (value.trim() === '') {
      setEmailError(null)
    } else if (!isValidEmail(value)) {
      setEmailError('Please enter a valid email address (e.g., user@example.com)')
    } else {
      setEmailError(null)
    }
  }

  const handleSubmit = () => {
    // Validate email before submission
    if (formData.email && !isValidEmail(formData.email)) {
      setEmailError('Please enter a valid email address')
      return
    }

    if (selectedUser) {
      // For editing, include email and password if provided
      const updateData: UserFormData = {
        username: formData.username,
        email: formData.email,
        password: formData.password || undefined, // Only include if provided
        role: formData.role,
        department: formData.department,
      }
      // Remove password if empty (don't update password)
      if (!updateData.password) {
        delete updateData.password
      }
      updateUser.mutate({ id: selectedUser.id, data: updateData })
    } else {
      // For creating, handle password generation
      let passwordToUse = formData.password
      if (formData.generatePassword) {
        passwordToUse = generateSecurePassword(12)
        setGeneratedPassword(passwordToUse)
      }
      
      const createData: UserFormData = {
        username: formData.username,
        email: formData.email,
        password: passwordToUse,
        role: formData.role,
        department: formData.department,
      }
      createUser.mutate(createData)
    }
  }

  const handleGeneratePasswordToggle = (checked: boolean) => {
    setFormData((prev) => ({ ...prev, generatePassword: checked, password: '' }))
    if (checked) {
      setShowPassword(false)
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
      id: 'email',
      header: 'Email',
      accessorKey: 'email',
      filterType: 'text',
      helpText: 'User email address used for authentication and password reset.',
      cell: (value) => value || '-',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessorKey: 'id',
      filterType: 'none',
      enableSorting: false,
      cell: (_, user) => (
        <div className="flex justify-center gap-2">
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
                disabled={!!selectedUser}
              />
            </div>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="email">Email</Label>
                <HelpIcon
                  content="User's email address. Required for password reset functionality."
                />
              </div>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleEmailChange(e.target.value)}
                placeholder="e.g., john.doe@example.com"
                className={emailError ? 'border-destructive' : ''}
              />
              {emailError && (
                <p className="text-sm text-destructive">{emailError}</p>
              )}
            </div>
            {selectedUser ? (
              <div className="grid gap-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="password">Set New Password (Optional)</Label>
                  <HelpIcon
                    content="Leave blank to keep current password. Enter a new password to change it."
                  />
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
                    placeholder="Enter new password (min 8 characters) or leave blank"
                    minLength={formData.password ? 8 : 0}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <div className="text-xs text-muted-foreground">
                  Leave blank to keep the current password unchanged.
                </div>
              </div>
            ) : (
              <div className="grid gap-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor="password">Password</Label>
                  <HelpIcon
                    content="Set a password for the user. You can auto-generate a secure password or enter one manually."
                  />
                </div>
                <div className="flex items-center space-x-2 mb-2">
                  <Checkbox
                    id="generate-password"
                    checked={formData.generatePassword}
                    onCheckedChange={handleGeneratePasswordToggle}
                  />
                  <Label
                    htmlFor="generate-password"
                    className="text-sm font-normal cursor-pointer"
                  >
                    Generate password automatically
                  </Label>
                </div>
                {!formData.generatePassword && (
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={formData.password}
                      onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
                      placeholder="Enter password (min 8 characters)"
                      minLength={8}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      tabIndex={-1}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                )}
                {formData.generatePassword && (
                  <div className="text-sm text-muted-foreground">
                    A secure password will be generated automatically when you create the user.
                  </div>
                )}
              </div>
            )}
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
            <Button
              onClick={handleSubmit}
              disabled={
                !formData.username ||
                (!selectedUser && (!formData.email || (!formData.generatePassword && !formData.password))) ||
                (selectedUser && !formData.email) ||
                !!emailError
              }
            >
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

