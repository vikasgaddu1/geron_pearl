import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Database, Plus, Trash2, RefreshCw, RotateCcw, Download, HardDrive } from 'lucide-react'
import { toast } from 'sonner'
import { databaseBackupApi } from '@/api'
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import type { DatabaseBackup as BackupType } from '@/types'
import { formatDateTime, getErrorMessage } from '@/lib/utils'

export function DatabaseBackup() {
  const queryClient = useQueryClient()
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false)
  const [selectedBackup, setSelectedBackup] = useState<BackupType | null>(null)
  const [description, setDescription] = useState('')

  // Queries
  const { data: backups = [], isLoading } = useQuery({
    queryKey: ['database-backups'],
    queryFn: databaseBackupApi.list,
  })

  const { data: status } = useQuery({
    queryKey: ['database-backup-status'],
    queryFn: databaseBackupApi.getStatus,
  })

  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['database-backups'] })
    queryClient.invalidateQueries({ queryKey: ['database-backup-status'] })
  }, [queryClient])

  // Mutations
  const createBackup = useMutation({
    mutationFn: () => databaseBackupApi.create(description || undefined),
    onSuccess: () => {
      toast.success('Backup created successfully')
      queryClient.invalidateQueries({ queryKey: ['database-backups'] })
      queryClient.invalidateQueries({ queryKey: ['database-backup-status'] })
      setCreateDialogOpen(false)
      setDescription('')
    },
    onError: (error) => toast.error(`Failed to create backup: ${getErrorMessage(error)}`),
  })

  const deleteBackup = useMutation({
    mutationFn: (filename: string) => databaseBackupApi.delete(filename),
    onSuccess: () => {
      toast.success('Backup deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['database-backups'] })
      queryClient.invalidateQueries({ queryKey: ['database-backup-status'] })
      setSelectedBackup(null)
    },
    onError: (error) => toast.error(`Failed to delete backup: ${getErrorMessage(error)}`),
  })

  const restoreBackup = useMutation({
    mutationFn: (filename: string) => databaseBackupApi.restore(filename),
    onSuccess: () => {
      toast.success('Database restored successfully')
      setRestoreDialogOpen(false)
      setSelectedBackup(null)
    },
    onError: (error) => toast.error(`Failed to restore backup: ${getErrorMessage(error)}`),
  })

  const handleDelete = (backup: BackupType) => {
    setSelectedBackup(backup)
    setDeleteDialogOpen(true)
  }

  const handleRestore = (backup: BackupType) => {
    setSelectedBackup(backup)
    setRestoreDialogOpen(true)
  }

  const confirmDelete = () => {
    if (selectedBackup) {
      deleteBackup.mutate(selectedBackup.filename)
      setDeleteDialogOpen(false)
    }
  }

  const confirmRestore = () => {
    if (selectedBackup) {
      restoreBackup.mutate(selectedBackup.filename)
    }
  }

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  if (isLoading) {
    return <PageLoader text="Loading backups..." />
  }

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              Database Backup
            </CardTitle>
            <CardDescription>
              Create and manage database backups
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={refetch}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button size="sm" onClick={() => setCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Backup
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Status Summary */}
          <div className="grid gap-4 md:grid-cols-3 mb-6">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <HardDrive className="h-8 w-8 text-primary" />
                  <div>
                    <p className="text-2xl font-bold">{status?.total_backups || 0}</p>
                    <p className="text-sm text-muted-foreground">Total Backups</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <Database className="h-8 w-8 text-green-500" />
                  <div>
                    <p className="text-sm font-medium">Latest Backup</p>
                    <p className="text-sm text-muted-foreground">
                      {status?.latest_backup
                        ? formatDateTime(status.latest_backup.created_at)
                        : 'None'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <Download className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium">Backup Directory</p>
                    <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                      {status?.backup_directory || 'Not configured'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Backups Table */}
          {backups.length === 0 ? (
            <EmptyState
              icon={Database}
              title="No backups found"
              description="Create your first backup to protect your data."
              action={{ label: 'Create Backup', onClick: () => setCreateDialogOpen(true) }}
            />
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Filename</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {backups.map((backup) => (
                    <TableRow key={backup.filename}>
                      <TableCell className="font-mono text-sm">{backup.filename}</TableCell>
                      <TableCell>{backup.description || '-'}</TableCell>
                      <TableCell>
                        <Badge variant="secondary">{formatSize(backup.size)}</Badge>
                      </TableCell>
                      <TableCell>{formatDateTime(backup.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRestore(backup)}
                            className="text-blue-600 hover:text-blue-700"
                          >
                            <RotateCcw className="h-4 w-4 mr-1" />
                            Restore
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(backup)}
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

      {/* Create Backup Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Database Backup</DialogTitle>
            <DialogDescription>
              Create a new backup of the current database state.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Input
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g., Before major update..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => createBackup.mutate()} disabled={createBackup.isPending}>
              {createBackup.isPending ? 'Creating...' : 'Create Backup'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Backup?"
        description={`Are you sure you want to delete "${selectedBackup?.filename}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={confirmDelete}
      />

      {/* Restore Confirmation */}
      <ConfirmDialog
        open={restoreDialogOpen}
        onOpenChange={setRestoreDialogOpen}
        title="Restore Database?"
        description={`Are you sure you want to restore the database from "${selectedBackup?.filename}"? This will overwrite all current data.`}
        confirmLabel="Restore"
        variant="destructive"
        onConfirm={confirmRestore}
        loading={restoreBackup.isPending}
      />
    </div>
  )
}


