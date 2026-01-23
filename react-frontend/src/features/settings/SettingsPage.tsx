import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Settings, Save, RefreshCw, User, Clock, Plus, Edit, Trash2, BookOpen, Tag, Shield, Check, AlertTriangle, Lock, FileSignature } from 'lucide-react'
import { toast } from 'sonner'
import {
  useAppSettings,
  useUpdateSettings,
  useIGVersions,
  useCreateIGVersion,
  useUpdateIGVersion,
  useDeleteIGVersion,
  useCasesApi,
  usersApi,
  tenantDataApi
} from '@/api'
import { SignatureSetupDialog } from './SignatureSetupDialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { HelpIcon } from '@/components/common/HelpIcon'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { Textarea } from '@/components/ui/textarea'
import { getErrorMessage, formatDateTime } from '@/lib/utils'
import { useAuthStore } from '@/stores/authStore'
import type { IGVersion, UseCase } from '@/types'

type StandardType = 'SDTM' | 'ADaM'

interface IGVersionFormData {
  standard_type: StandardType
  version: string
  description: string
  is_active: boolean
}

const defaultFormData: IGVersionFormData = {
  standard_type: 'SDTM',
  version: '',
  description: '',
  is_active: true,
}

interface UseCaseFormData {
  name: string
  color: string
  description: string
}

const defaultUseCaseFormData: UseCaseFormData = {
  name: '',
  color: '#3B82F6',
  description: '',
}

const colorOptions = [
  { color: '#3B82F6', name: 'Blue' },
  { color: '#10B981', name: 'Green' },
  { color: '#F59E0B', name: 'Amber' },
  { color: '#EF4444', name: 'Red' },
  { color: '#8B5CF6', name: 'Purple' },
  { color: '#EC4899', name: 'Pink' },
  { color: '#6366F1', name: 'Indigo' },
  { color: '#14B8A6', name: 'Teal' },
]

export function SettingsPage() {
  const queryClient = useQueryClient()
  const { data: settings, isLoading, refetch } = useAppSettings()
  const updateSettings = useUpdateSettings()
  const { data: igVersions = [], isLoading: igVersionsLoading, refetch: refetchIGVersions } = useIGVersions()
  const createIGVersion = useCreateIGVersion()
  const updateIGVersion = useUpdateIGVersion()
  const deleteIGVersion = useDeleteIGVersion()

  // Use Cases queries and mutations
  const { data: useCases = [], isLoading: useCasesLoading, refetch: refetchUseCases } = useQuery({
    queryKey: ['use-cases'],
    queryFn: useCasesApi.getAllUseCases,
  })

  const createUseCase = useMutation({
    mutationFn: useCasesApi.createUseCase,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['use-cases'] })
    },
  })

  const updateUseCase = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<UseCaseFormData> }) =>
      useCasesApi.updateUseCase(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['use-cases'] })
    },
  })

  const deleteUseCase = useMutation({
    mutationFn: useCasesApi.deleteUseCase,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['use-cases'] })
    },
  })

  const [dueDateOffset, setDueDateOffset] = useState<number>(7)
  const [hasChanges, setHasChanges] = useState(false)

  // IG Version dialog state
  const [igDialogOpen, setIgDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [editingVersion, setEditingVersion] = useState<IGVersion | null>(null)
  const [formData, setFormData] = useState<IGVersionFormData>(defaultFormData)

  // Use Case dialog state
  const [useCaseDialogOpen, setUseCaseDialogOpen] = useState(false)
  const [useCaseDeleteDialogOpen, setUseCaseDeleteDialogOpen] = useState(false)
  const [editingUseCase, setEditingUseCase] = useState<UseCase | null>(null)
  const [useCaseFormData, setUseCaseFormData] = useState<UseCaseFormData>(defaultUseCaseFormData)

  // Signature setup dialog state
  const [signatureSetupOpen, setSignatureSetupOpen] = useState(false)

  // Signature status query
  const { data: signatureStatus, refetch: refetchSignatureStatus } = useQuery({
    queryKey: ['signature-status'],
    queryFn: usersApi.getSignatureStatus,
  })

  // Signature lock setting query (admin only)
  const { currentUser } = useAuthStore()
  const isAdmin = currentUser?.is_admin === true

  const { data: signatureLockSetting, refetch: refetchSignatureLockSetting } = useQuery({
    queryKey: ['tenant-signature-lock-setting'],
    queryFn: tenantDataApi.getSignatureLockSetting,
    enabled: isAdmin,
  })

  const updateSignatureLockSetting = useMutation({
    mutationFn: (value: boolean) => tenantDataApi.updateSignatureLockSetting(value),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenant-signature-lock-setting'] })
    },
  })

  // Sync local state with fetched settings
  useEffect(() => {
    if (settings) {
      setDueDateOffset(settings.default_due_date_offset)
      setHasChanges(false)
    }
  }, [settings])

  // Track changes
  useEffect(() => {
    if (settings) {
      setHasChanges(dueDateOffset !== settings.default_due_date_offset)
    }
  }, [dueDateOffset, settings])

  const handleSave = async () => {
    if (!hasChanges) return

    try {
      await updateSettings.mutateAsync({
        default_due_date_offset: dueDateOffset,
      })
      toast.success('Settings saved successfully')
    } catch (error) {
      toast.error(`Failed to save settings: ${getErrorMessage(error)}`)
    }
  }

  const handleReset = () => {
    if (settings) {
      setDueDateOffset(settings.default_due_date_offset)
    }
  }

  // IG Version handlers
  const handleAddVersion = () => {
    setEditingVersion(null)
    setFormData(defaultFormData)
    setIgDialogOpen(true)
  }

  const handleEditVersion = (version: IGVersion) => {
    setEditingVersion(version)
    setFormData({
      standard_type: version.standard_type as StandardType,
      version: version.version,
      description: version.description || '',
      is_active: version.is_active,
    })
    setIgDialogOpen(true)
  }

  const handleDeleteVersion = (version: IGVersion) => {
    setEditingVersion(version)
    setDeleteDialogOpen(true)
  }

  const handleSubmitVersion = async () => {
    if (!formData.version.trim()) {
      toast.error('Version number is required')
      return
    }

    try {
      if (editingVersion) {
        await updateIGVersion.mutateAsync({
          id: editingVersion.id,
          data: {
            standard_type: formData.standard_type,
            version: formData.version.trim(),
            description: formData.description.trim() || undefined,
            is_active: formData.is_active,
          },
        })
        toast.success('IG version updated successfully')
      } else {
        await createIGVersion.mutateAsync({
          standard_type: formData.standard_type,
          version: formData.version.trim(),
          description: formData.description.trim() || undefined,
          is_active: formData.is_active,
        })
        toast.success('IG version created successfully')
      }
      setIgDialogOpen(false)
      setFormData(defaultFormData)
      setEditingVersion(null)
    } catch (error) {
      toast.error(`Failed to save IG version: ${getErrorMessage(error)}`)
    }
  }

  const confirmDelete = async () => {
    if (!editingVersion) return

    try {
      await deleteIGVersion.mutateAsync(editingVersion.id)
      toast.success('IG version deleted successfully')
      setDeleteDialogOpen(false)
      setEditingVersion(null)
    } catch (error) {
      toast.error(`Failed to delete IG version: ${getErrorMessage(error)}`)
    }
  }

  // Group IG versions by type
  const sdtmVersions = igVersions.filter(v => v.standard_type === 'SDTM')
  const adamVersions = igVersions.filter(v => v.standard_type === 'ADaM')

  // Use Case handlers
  const handleAddUseCase = () => {
    setEditingUseCase(null)
    setUseCaseFormData(defaultUseCaseFormData)
    setUseCaseDialogOpen(true)
  }

  const handleEditUseCase = (useCase: UseCase) => {
    setEditingUseCase(useCase)
    setUseCaseFormData({
      name: useCase.name,
      color: useCase.color,
      description: useCase.description || '',
    })
    setUseCaseDialogOpen(true)
  }

  const handleDeleteUseCase = (useCase: UseCase) => {
    setEditingUseCase(useCase)
    setUseCaseDeleteDialogOpen(true)
  }

  const handleSubmitUseCase = async () => {
    if (!useCaseFormData.name.trim()) {
      toast.error('Name is required')
      return
    }

    try {
      if (editingUseCase) {
        await updateUseCase.mutateAsync({
          id: editingUseCase.id,
          data: {
            name: useCaseFormData.name.trim(),
            color: useCaseFormData.color,
            description: useCaseFormData.description.trim() || undefined,
          },
        })
        toast.success('Use case updated successfully')
      } else {
        await createUseCase.mutateAsync({
          name: useCaseFormData.name.trim(),
          color: useCaseFormData.color,
          description: useCaseFormData.description.trim() || undefined,
        })
        toast.success('Use case created successfully')
      }
      setUseCaseDialogOpen(false)
      setUseCaseFormData(defaultUseCaseFormData)
      setEditingUseCase(null)
    } catch (error) {
      toast.error(`Failed to save use case: ${getErrorMessage(error)}`)
    }
  }

  const confirmDeleteUseCase = async () => {
    if (!editingUseCase) return

    try {
      await deleteUseCase.mutateAsync(editingUseCase.id)
      toast.success('Use case deleted successfully')
      setUseCaseDeleteDialogOpen(false)
      setEditingUseCase(null)
    } catch (error) {
      toast.error(`Failed to delete use case: ${getErrorMessage(error)}`)
    }
  }

  if (isLoading) {
    return <PageLoader text="Loading settings..." />
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Settings className="h-6 w-6 text-primary" />
            Application Settings
          </h1>
          <p className="text-muted-foreground mt-1">
            Configure application-wide settings. Changes take effect immediately.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => { refetch(); refetchIGVersions(); refetchUseCases(); }}
            disabled={updateSettings.isPending}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            Due Date Settings
          </CardTitle>
          <CardDescription>
            Configure default values for tracker due dates
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="due-date-offset">Default Due Date Offset</Label>
              <HelpIcon content="When a production programmer is assigned to a tracker without an existing due date, the due date will automatically be set to today plus this number of days." />
            </div>
            <div className="flex items-center gap-4">
              <Input
                id="due-date-offset"
                type="number"
                min={1}
                max={365}
                value={dueDateOffset}
                onChange={(e) => setDueDateOffset(parseInt(e.target.value) || 1)}
                className="w-24"
              />
              <span className="text-muted-foreground">days</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Valid range: 1 to 365 days. Current setting: {settings?.default_due_date_offset || 7} days.
            </p>
          </div>

          <div className="flex items-center justify-between pt-4 border-t">
            <div className="text-sm text-muted-foreground">
              {settings?.updated_by_username && (
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Last updated by {settings.updated_by_username} on{' '}
                  {formatDateTime(settings.updated_at)}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              {hasChanges && (
                <Button variant="outline" onClick={handleReset}>
                  Reset
                </Button>
              )}
              <Button
                onClick={handleSave}
                disabled={!hasChanges || updateSettings.isPending}
              >
                {updateSettings.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* IG Versions Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-primary" />
                Implementation Guide Versions
              </CardTitle>
              <CardDescription>
                Manage SDTM and ADaM Implementation Guide versions available for dataset items
              </CardDescription>
            </div>
            <Button size="sm" onClick={handleAddVersion}>
              <Plus className="h-4 w-4 mr-2" />
              Add Version
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {igVersionsLoading ? (
            <div className="text-center py-4 text-muted-foreground">Loading IG versions...</div>
          ) : igVersions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No IG versions configured yet.</p>
              <p className="text-sm">Click "Add Version" to create one.</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-6">
              {/* SDTM Versions */}
              <div className="space-y-3">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <Badge variant="default">SDTM</Badge>
                  Versions ({sdtmVersions.length})
                </h3>
                {sdtmVersions.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-2">No SDTM versions configured.</p>
                ) : (
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Version</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {sdtmVersions.map((version) => (
                          <TableRow key={version.id}>
                            <TableCell className="font-medium">
                              {version.version}
                              {version.description && (
                                <span className="text-xs text-muted-foreground ml-2">
                                  ({version.description})
                                </span>
                              )}
                            </TableCell>
                            <TableCell>
                              <Badge variant={version.is_active ? 'success' : 'secondary'}>
                                {version.is_active ? 'Active' : 'Inactive'}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-1">
                                <Button variant="ghost" size="icon" onClick={() => handleEditVersion(version)}>
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button variant="ghost" size="icon" onClick={() => handleDeleteVersion(version)}>
                                  <Trash2 className="h-4 w-4 text-destructive" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>

              {/* ADaM Versions */}
              <div className="space-y-3">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <Badge variant="secondary">ADaM</Badge>
                  Versions ({adamVersions.length})
                </h3>
                {adamVersions.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-2">No ADaM versions configured.</p>
                ) : (
                  <div className="rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Version</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {adamVersions.map((version) => (
                          <TableRow key={version.id}>
                            <TableCell className="font-medium">
                              {version.version}
                              {version.description && (
                                <span className="text-xs text-muted-foreground ml-2">
                                  ({version.description})
                                </span>
                              )}
                            </TableCell>
                            <TableCell>
                              <Badge variant={version.is_active ? 'success' : 'secondary'}>
                                {version.is_active ? 'Active' : 'Inactive'}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-1">
                                <Button variant="ghost" size="icon" onClick={() => handleEditVersion(version)}>
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button variant="ghost" size="icon" onClick={() => handleDeleteVersion(version)}>
                                  <Trash2 className="h-4 w-4 text-destructive" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Signature Authentication Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Signature Authentication
          </CardTitle>
          <CardDescription>
            Set up two-factor authentication for electronic signatures on reporting efforts
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
            <div className="flex items-center gap-3">
              {signatureStatus?.is_setup_completed ? (
                <>
                  <div className="h-10 w-10 rounded-full bg-green-500/20 flex items-center justify-center">
                    <Check className="h-5 w-5 text-green-500" />
                  </div>
                  <div>
                    <p className="font-medium text-green-600 dark:text-green-400">
                      Authentication Set Up
                    </p>
                    <p className="text-sm text-muted-foreground">
                      You can sign reporting efforts using your authenticator app
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <div className="h-10 w-10 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <AlertTriangle className="h-5 w-5 text-amber-500" />
                  </div>
                  <div>
                    <p className="font-medium text-amber-600 dark:text-amber-400">
                      Not Set Up
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Set up authentication to sign reporting efforts
                    </p>
                  </div>
                </>
              )}
            </div>
            <Button
              variant={signatureStatus?.is_setup_completed ? 'outline' : 'default'}
              onClick={() => setSignatureSetupOpen(true)}
            >
              {signatureStatus?.is_setup_completed ? 'Manage' : 'Set Up'}
            </Button>
          </div>

          <div className="text-sm text-muted-foreground space-y-2">
            <p><strong>What is this?</strong></p>
            <p>
              Electronic signatures provide a regulatory-grade sign-off for reporting efforts.
              Once all items in a reporting effort are marked "In Production", authorized users
              (Admin or Study LEAD) can sign the effort to permanently lock it.
            </p>
            <p>
              Signing requires a 6-digit code from an authenticator app (like Google Authenticator
              or Authy) that changes every 30 seconds.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Lock Behavior Settings Card - Admin only */}
      {isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5 text-primary" />
              Lock Behavior Settings
            </CardTitle>
            <CardDescription>
              Configure how reporting effort locking works for your organization
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div className="flex items-center gap-3">
                <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                  signatureLockSetting?.signature_locks_effort
                    ? 'bg-blue-500/20'
                    : 'bg-amber-500/20'
                }`}>
                  {signatureLockSetting?.signature_locks_effort ? (
                    <FileSignature className="h-5 w-5 text-blue-500" />
                  ) : (
                    <Lock className="h-5 w-5 text-amber-500" />
                  )}
                </div>
                <div>
                  <p className="font-medium">
                    {signatureLockSetting?.signature_locks_effort
                      ? 'Signing Locks Automatically'
                      : 'Manual Lock/Unlock Enabled'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {signatureLockSetting?.signature_locks_effort
                      ? 'Signing a reporting effort automatically locks it. No separate lock/unlock controls.'
                      : 'Lock/unlock is manual and independent of signing. No phone/authenticator required for locking.'}
                  </p>
                </div>
              </div>
              <Switch
                checked={signatureLockSetting?.signature_locks_effort ?? true}
                onCheckedChange={async (checked) => {
                  try {
                    await updateSignatureLockSetting.mutateAsync(checked)
                    toast.success(checked
                      ? 'Signing will now automatically lock reporting efforts'
                      : 'Manual lock/unlock is now enabled'
                    )
                  } catch (error) {
                    toast.error(`Failed to update setting: ${getErrorMessage(error)}`)
                  }
                }}
                disabled={updateSignatureLockSetting.isPending}
              />
            </div>

            <div className="text-sm text-muted-foreground space-y-2 border-t pt-4">
              <p><strong>Options explained:</strong></p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>
                  <strong>On (Default):</strong> Signing automatically locks the reporting effort.
                  Manual lock/unlock buttons are hidden. This is the recommended setting for
                  regulatory compliance workflows.
                </li>
                <li>
                  <strong>Off:</strong> Lock/unlock is a separate action from signing.
                  Manual lock/unlock buttons are shown. Use this if you need flexibility
                  during QC review cycles or don't want phone dependency for locking.
                </li>
              </ul>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Use Cases Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Tag className="h-5 w-5 text-primary" />
                Use Cases
              </CardTitle>
              <CardDescription>
                Manage use cases that can be assigned to reporting efforts for categorization and reporting
              </CardDescription>
            </div>
            <Button size="sm" onClick={handleAddUseCase}>
              <Plus className="h-4 w-4 mr-2" />
              Add Use Case
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {useCasesLoading ? (
            <div className="text-center py-4 text-muted-foreground">Loading use cases...</div>
          ) : useCases.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Tag className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No use cases configured yet.</p>
              <p className="text-sm">Click "Add Use Case" to create one.</p>
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Color</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Usage</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {useCases.map((useCase: UseCase) => (
                    <TableRow key={useCase.id}>
                      <TableCell>
                        <div
                          className="w-6 h-6 rounded-full border"
                          style={{ backgroundColor: useCase.color }}
                        />
                      </TableCell>
                      <TableCell className="font-medium">{useCase.name}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {useCase.description || '-'}
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{useCase.usage_count || 0} efforts</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon" onClick={() => handleEditUseCase(useCase)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteUseCase(useCase)}
                            disabled={(useCase.usage_count || 0) > 0}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>


      {/* Add/Edit IG Version Dialog */}
      <Dialog open={igDialogOpen} onOpenChange={setIgDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingVersion ? 'Edit IG Version' : 'Add IG Version'}
            </DialogTitle>
            <DialogDescription>
              {editingVersion 
                ? 'Update the Implementation Guide version details.' 
                : 'Add a new Implementation Guide version for SDTM or ADaM datasets.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Standard Type</Label>
              <Select
                value={formData.standard_type}
                onValueChange={(value: StandardType) => 
                  setFormData(prev => ({ ...prev, standard_type: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="SDTM">SDTM</SelectItem>
                  <SelectItem value="ADaM">ADaM</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="version">Version Number</Label>
              <Input
                id="version"
                value={formData.version}
                onChange={(e) => setFormData(prev => ({ ...prev, version: e.target.value }))}
                placeholder="e.g., 3.4 or 1.2"
              />
              <p className="text-xs text-muted-foreground">
                Enter the version number without the 'v' prefix (e.g., 3.4 for SDTM v3.4)
              </p>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Input
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="e.g., SDTM Implementation Guide v3.4"
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="is_active">Active</Label>
                <p className="text-xs text-muted-foreground">
                  Inactive versions won't appear in dropdowns
                </p>
              </div>
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => 
                  setFormData(prev => ({ ...prev, is_active: checked }))
                }
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIgDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmitVersion} 
              disabled={!formData.version.trim() || createIGVersion.isPending || updateIGVersion.isPending}
            >
              {(createIGVersion.isPending || updateIGVersion.isPending) ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                editingVersion ? 'Update' : 'Create'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete IG Version?"
        description={`Are you sure you want to delete ${editingVersion?.standard_type} v${editingVersion?.version}? This will fail if the version is in use by any datasets.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={confirmDelete}
      />

      {/* Add/Edit Use Case Dialog */}
      <Dialog open={useCaseDialogOpen} onOpenChange={setUseCaseDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingUseCase ? 'Edit Use Case' : 'Add Use Case'}
            </DialogTitle>
            <DialogDescription>
              {editingUseCase
                ? 'Update the use case details.'
                : 'Create a new use case to categorize reporting efforts.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="use-case-name">Name</Label>
              <Input
                id="use-case-name"
                value={useCaseFormData.name}
                onChange={(e) => setUseCaseFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Clinical, Publication, Labeling"
              />
            </div>
            <div className="grid gap-2">
              <Label>Color</Label>
              <div className="flex flex-wrap gap-2">
                {colorOptions.map(({ color, name }) => (
                  <button
                    key={color}
                    type="button"
                    onClick={() => setUseCaseFormData(prev => ({ ...prev, color }))}
                    className={`w-8 h-8 rounded-full border-2 transition-all ${
                      useCaseFormData.color === color
                        ? 'border-foreground scale-110'
                        : 'border-transparent hover:scale-105'
                    }`}
                    style={{ backgroundColor: color }}
                    title={name}
                  />
                ))}
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="use-case-description">Description (Optional)</Label>
              <Textarea
                id="use-case-description"
                value={useCaseFormData.description}
                onChange={(e) => setUseCaseFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Brief description of this use case..."
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUseCaseDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmitUseCase}
              disabled={!useCaseFormData.name.trim() || createUseCase.isPending || updateUseCase.isPending}
            >
              {(createUseCase.isPending || updateUseCase.isPending) ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                editingUseCase ? 'Update' : 'Create'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Use Case Confirmation */}
      <ConfirmDialog
        open={useCaseDeleteDialogOpen}
        onOpenChange={setUseCaseDeleteDialogOpen}
        title="Delete Use Case?"
        description={`Are you sure you want to delete "${editingUseCase?.name}"? This will remove it from all assigned reporting efforts.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={confirmDeleteUseCase}
      />

      {/* Signature Setup Dialog */}
      <SignatureSetupDialog
        open={signatureSetupOpen}
        onOpenChange={(open) => {
          setSignatureSetupOpen(open)
          if (!open) {
            refetchSignatureStatus()
          }
        }}
      />
    </div>
  )
}
