import { useState, useEffect } from 'react'
import { Settings, Save, RefreshCw, User, Clock, Plus, Edit, Trash2, BookOpen } from 'lucide-react'
import { toast } from 'sonner'
import { 
  useAppSettings, 
  useUpdateSettings, 
  useIGVersions,
  useCreateIGVersion,
  useUpdateIGVersion,
  useDeleteIGVersion 
} from '@/api'
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
import { getErrorMessage, formatDateTime } from '@/lib/utils'
import type { IGVersion } from '@/types'

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

export function SettingsPage() {
  const { data: settings, isLoading, refetch } = useAppSettings()
  const updateSettings = useUpdateSettings()
  const { data: igVersions = [], isLoading: igVersionsLoading, refetch: refetchIGVersions } = useIGVersions()
  const createIGVersion = useCreateIGVersion()
  const updateIGVersion = useUpdateIGVersion()
  const deleteIGVersion = useDeleteIGVersion()

  const [dueDateOffset, setDueDateOffset] = useState<number>(7)
  const [hasChanges, setHasChanges] = useState(false)
  
  // IG Version dialog state
  const [igDialogOpen, setIgDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [editingVersion, setEditingVersion] = useState<IGVersion | null>(null)
  const [formData, setFormData] = useState<IGVersionFormData>(defaultFormData)

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
            onClick={() => { refetch(); refetchIGVersions(); }}
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
    </div>
  )
}
