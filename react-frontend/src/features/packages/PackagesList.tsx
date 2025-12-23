import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Package, Plus, Edit, Trash2, RefreshCw, Eye } from 'lucide-react'
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'
import { packagesApi } from '@/api'
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
import { DataTable, ColumnDef } from '@/components/common/DataTable'
import { TooltipWrapper } from '@/components/common/TooltipWrapper'
import { HelpIcon } from '@/components/common/HelpIcon'
import { useWebSocketRefresh } from '@/hooks/useWebSocket'
import type { Package as PackageType, PackageFormData } from '@/types'
import { formatDateTime } from '@/lib/utils'

export function PackagesList() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedPackage, setSelectedPackage] = useState<PackageType | null>(null)
  const [formData, setFormData] = useState<PackageFormData>({
    package_name: '',
    study_indication: '',
    therapeutic_area: '',
  })

  // Query
  const { data: packages = [], isLoading } = useQuery({
    queryKey: ['packages'],
    queryFn: packagesApi.getAll,
  })

  // WebSocket refresh
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['packages'] })
  }, [queryClient])

  useWebSocketRefresh(['package'], refetch)

  // Mutations
  const createPackage = useMutation({
    mutationFn: packagesApi.create,
    onSuccess: () => {
      toast.success('Package created successfully')
      queryClient.invalidateQueries({ queryKey: ['packages'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: () => toast.error('Failed to create package'),
  })

  const updatePackage = useMutation({
    mutationFn: ({ id, data }: { id: number; data: PackageFormData }) =>
      packagesApi.update(id, data),
    onSuccess: () => {
      toast.success('Package updated successfully')
      queryClient.invalidateQueries({ queryKey: ['packages'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: () => toast.error('Failed to update package'),
  })

  const deletePackage = useMutation({
    mutationFn: packagesApi.delete,
    onSuccess: () => {
      toast.success('Package deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['packages'] })
      setSelectedPackage(null)
    },
    onError: () => toast.error('Failed to delete package. It may have items.'),
  })

  const resetForm = () => {
    setFormData({ package_name: '', study_indication: '', therapeutic_area: '' })
    setSelectedPackage(null)
  }

  const handleAdd = () => {
    resetForm()
    setDialogOpen(true)
  }

  const handleEdit = (pkg: PackageType) => {
    setSelectedPackage(pkg)
    setFormData({
      package_name: pkg.package_name,
      study_indication: pkg.study_indication || '',
      therapeutic_area: pkg.therapeutic_area || '',
    })
    setDialogOpen(true)
  }

  const handleDelete = (pkg: PackageType) => {
    setSelectedPackage(pkg)
    setDeleteDialogOpen(true)
  }

  const handleSubmit = () => {
    if (selectedPackage) {
      updatePackage.mutate({ id: selectedPackage.id, data: formData })
    } else {
      createPackage.mutate(formData)
    }
  }

  const confirmDelete = () => {
    if (selectedPackage) {
      deletePackage.mutate(selectedPackage.id)
      setDeleteDialogOpen(false)
    }
  }

  // Define table columns
  const columns: ColumnDef<PackageType>[] = [
    {
      id: 'package_name',
      header: 'Package Name',
      accessorKey: 'package_name',
      filterType: 'text',
      helpText: 'Unique name for the package containing TLF and dataset templates.',
      cell: (value) => <span className="font-medium">{value}</span>,
    },
    {
      id: 'study_indication',
      header: 'Study Indication',
      accessorKey: 'study_indication',
      filterType: 'select',
      helpText: 'The medical condition or disease being studied in this package.',
      cell: (value) => value || '-',
    },
    {
      id: 'therapeutic_area',
      header: 'Therapeutic Area',
      accessorKey: 'therapeutic_area',
      filterType: 'select',
      helpText: 'The broad therapeutic category this package falls under (e.g., Oncology, Cardiology).',
      cell: (value) => value || '-',
    },
    {
      id: 'created_at',
      header: 'Created',
      accessorKey: 'created_at',
      filterType: 'date',
      helpText: 'Date and time when this package was created.',
      cell: (value) => formatDateTime(value),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessorKey: 'id',
      filterType: 'none',
      enableSorting: false,
      cell: (_, pkg) => (
        <div className="flex justify-end gap-2">
          <TooltipWrapper content="View package items">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(`/package-items?package=${pkg.id}`)}
            >
              <Eye className="h-4 w-4" />
            </Button>
          </TooltipWrapper>
          <TooltipWrapper content="Edit package">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleEdit(pkg)}
            >
              <Edit className="h-4 w-4" />
            </Button>
          </TooltipWrapper>
          <TooltipWrapper content="Delete package">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDelete(pkg)}
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </TooltipWrapper>
        </div>
      ),
    },
  ]

  if (isLoading) {
    return <PageLoader text="Loading packages..." />
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div className="flex items-center gap-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5 text-primary" />
                Packages
              </CardTitle>
              <CardDescription>
                Manage TLF and dataset template packages
              </CardDescription>
            </div>
            <HelpIcon
              title="Package Management"
              content="Packages are collections of TLF (Tables, Listings, Figures) and dataset templates that can be reused across studies. Each package can contain multiple items with associated properties."
            />
          </div>
          <div className="flex gap-2">
            <TooltipWrapper content="Refresh package list">
              <Button variant="outline" size="sm" onClick={refetch}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </TooltipWrapper>
            <TooltipWrapper content="Create a new package">
              <Button size="sm" onClick={handleAdd}>
                <Plus className="h-4 w-4 mr-2" />
                Add Package
              </Button>
            </TooltipWrapper>
          </div>
        </CardHeader>
        <CardContent>
          {packages.length === 0 ? (
            <EmptyState
              icon={Package}
              title="No packages found"
              description="Get started by creating a package."
              action={{ label: 'Add Package', onClick: handleAdd }}
            />
          ) : (
            <DataTable data={packages} columns={columns} />
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedPackage ? 'Edit Package' : 'Add New Package'}</DialogTitle>
            <DialogDescription>
              {selectedPackage ? 'Update package information.' : 'Create a new template package.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="package_name">Package Name</Label>
                <HelpIcon content="Enter a unique name for this package. This will be used to identify the collection of templates." />
              </div>
              <Input
                id="package_name"
                value={formData.package_name}
                onChange={(e) => setFormData((prev) => ({ ...prev, package_name: e.target.value }))}
                placeholder="e.g., ONCOLOGY_BASELINE_PKG"
              />
            </div>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="study_indication">Study Indication (Optional)</Label>
                <HelpIcon content="Specify the medical condition or disease this package is designed for." />
              </div>
              <Input
                id="study_indication"
                value={formData.study_indication}
                onChange={(e) => setFormData((prev) => ({ ...prev, study_indication: e.target.value }))}
                placeholder="e.g., Breast Cancer, Type 2 Diabetes"
              />
            </div>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="therapeutic_area">Therapeutic Area (Optional)</Label>
                <HelpIcon content="Enter the broad therapeutic category (e.g., Oncology, Cardiovascular, Neurology)." />
              </div>
              <Input
                id="therapeutic_area"
                value={formData.therapeutic_area}
                onChange={(e) => setFormData((prev) => ({ ...prev, therapeutic_area: e.target.value }))}
                placeholder="e.g., Oncology, Immunology"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!formData.package_name}>
              {selectedPackage ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Package?"
        description={`Are you sure you want to delete "${selectedPackage?.package_name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={confirmDelete}
      />
    </div>
  )
}

