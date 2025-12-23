import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ClipboardList, Plus, Edit, Trash2, RefreshCw, Search, Copy, Upload, CheckSquare } from 'lucide-react'
import { toast } from 'sonner'
import { reportingEffortsApi, reportingEffortItemsApi, packagesApi } from '@/api'
import { getErrorMessage } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
import { useWebSocketRefresh } from '@/hooks/useWebSocket'
import type { ReportingEffortItem, ItemType, ItemSubtype } from '@/types'

const ITEM_TYPES: ItemType[] = ['TLF', 'Dataset']
const TLF_SUBTYPES: ItemSubtype[] = ['Table', 'Listing', 'Figure']
const DATASET_SUBTYPES: ItemSubtype[] = ['SDTM', 'ADaM']
const ITEM_STATUSES = ['PENDING', 'IN_PROGRESS', 'COMPLETED'] as const

type TabType = 'tlf' | 'sdtm' | 'adam'

export function ReportingEffortItems() {
  const queryClient = useQueryClient()
  const [selectedEffortId, setSelectedEffortId] = useState<string>('')
  const [activeTab, setActiveTab] = useState<TabType>('tlf')
  const [search, setSearch] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [copyDialogOpen, setCopyDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [bulkEditOpen, setBulkEditOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ReportingEffortItem | null>(null)
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())
  const [copySource, setCopySource] = useState<{ type: 'package' | 'effort'; id: string }>({ type: 'package', id: '' })
  const [formData, setFormData] = useState({
    item_code: '',
    item_description: '',
    item_type: 'TLF' as ItemType,
    item_subtype: 'Table' as ItemSubtype,
  })
  const [bulkFormData, setBulkFormData] = useState({
    item_status: '' as string,
  })

  // Queries
  const { data: efforts = [], isLoading: effortsLoading } = useQuery({
    queryKey: ['reporting-efforts'],
    queryFn: reportingEffortsApi.getAll,
  })

  const { data: packages = [] } = useQuery({
    queryKey: ['packages'],
    queryFn: packagesApi.getAll,
  })

  const { data: items = [], isLoading: itemsLoading } = useQuery({
    queryKey: ['reporting-effort-items', selectedEffortId],
    queryFn: () => (selectedEffortId ? reportingEffortItemsApi.getByEffortId(Number(selectedEffortId)) : Promise.resolve([])),
    enabled: !!selectedEffortId,
  })

  // WebSocket refresh
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['reporting-effort-items', selectedEffortId] })
  }, [queryClient, selectedEffortId])

  useWebSocketRefresh(['reporting_effort_item'], refetch)

  // Mutations
  const createItem = useMutation({
    mutationFn: (data: Partial<ReportingEffortItem>) =>
      reportingEffortItemsApi.create({ ...data, reporting_effort_id: Number(selectedEffortId) }),
    onSuccess: () => {
      toast.success('Item created successfully')
      queryClient.invalidateQueries({ queryKey: ['reporting-effort-items', selectedEffortId] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error) => toast.error(`Failed to create item: ${getErrorMessage(error)}`),
  })

  const updateItem = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ReportingEffortItem> }) =>
      reportingEffortItemsApi.update(id, data),
    onSuccess: () => {
      toast.success('Item updated successfully')
      queryClient.invalidateQueries({ queryKey: ['reporting-effort-items', selectedEffortId] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error) => toast.error(`Failed to update item: ${getErrorMessage(error)}`),
  })

  const deleteItem = useMutation({
    mutationFn: reportingEffortItemsApi.delete,
    onSuccess: () => {
      toast.success('Item deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['reporting-effort-items', selectedEffortId] })
      setSelectedItem(null)
    },
    onError: (error) => toast.error(`Failed to delete item: ${getErrorMessage(error)}`),
  })

  const copyFromPackage = useMutation({
    mutationFn: () => reportingEffortItemsApi.copyFromPackage(Number(selectedEffortId), Number(copySource.id)),
    onSuccess: (result) => {
      toast.success(`Copied ${result.created} items from package`)
      queryClient.invalidateQueries({ queryKey: ['reporting-effort-items', selectedEffortId] })
      setCopyDialogOpen(false)
    },
    onError: (error) => toast.error(`Failed to copy from package: ${getErrorMessage(error)}`),
  })

  const copyFromEffort = useMutation({
    mutationFn: () => reportingEffortItemsApi.copyFromReportingEffort(Number(selectedEffortId), Number(copySource.id)),
    onSuccess: (result) => {
      toast.success(`Copied ${result.created} items from reporting effort`)
      queryClient.invalidateQueries({ queryKey: ['reporting-effort-items', selectedEffortId] })
      setCopyDialogOpen(false)
    },
    onError: (error) => toast.error(`Failed to copy from reporting effort: ${getErrorMessage(error)}`),
  })

  const resetForm = () => {
    setFormData({
      item_code: '',
      item_description: '',
      item_type: 'TLF',
      item_subtype: 'Table',
    })
    setSelectedItem(null)
  }

  const handleAdd = () => {
    resetForm()
    // Set default type based on active tab
    if (activeTab === 'tlf') {
      setFormData(prev => ({ ...prev, item_type: 'TLF', item_subtype: 'Table' }))
    } else if (activeTab === 'sdtm') {
      setFormData(prev => ({ ...prev, item_type: 'Dataset', item_subtype: 'SDTM' }))
    } else {
      setFormData(prev => ({ ...prev, item_type: 'Dataset', item_subtype: 'ADaM' }))
    }
    setDialogOpen(true)
  }

  const handleEdit = (item: ReportingEffortItem) => {
    setSelectedItem(item)
    setFormData({
      item_code: item.item_code,
      item_description: item.item_description || '',
      item_type: item.item_type,
      item_subtype: item.item_subtype || 'Table',
    })
    setDialogOpen(true)
  }

  const handleDelete = (item: ReportingEffortItem) => {
    setSelectedItem(item)
    setDeleteDialogOpen(true)
  }

  const handleSubmit = () => {
    const data = {
      item_code: formData.item_code,
      item_description: formData.item_description,
      item_type: formData.item_type,
      item_subtype: formData.item_subtype,
    }
    if (selectedItem) {
      updateItem.mutate({ id: selectedItem.id, data })
    } else {
      createItem.mutate(data)
    }
  }

  const handleCopy = () => {
    if (copySource.type === 'package') {
      copyFromPackage.mutate()
    } else {
      copyFromEffort.mutate()
    }
  }

  const confirmDelete = () => {
    if (selectedItem) {
      deleteItem.mutate(selectedItem.id)
      setDeleteDialogOpen(false)
    }
  }

  // Bulk edit handlers
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedRows(new Set(filteredItems.map((item) => item.id)))
    } else {
      setSelectedRows(new Set())
    }
  }

  const handleSelectRow = (id: number, checked: boolean) => {
    const newSelected = new Set(selectedRows)
    if (checked) {
      newSelected.add(id)
    } else {
      newSelected.delete(id)
    }
    setSelectedRows(newSelected)
  }

  const handleBulkEdit = async () => {
    if (!bulkFormData.item_status) {
      toast.error('Please select a status')
      return
    }
    
    // Update each selected item
    const promises = Array.from(selectedRows).map(id =>
      reportingEffortItemsApi.update(id, { item_status: bulkFormData.item_status as ReportingEffortItem['item_status'] })
    )
    
    try {
      await Promise.all(promises)
      toast.success(`Updated ${selectedRows.size} items`)
      queryClient.invalidateQueries({ queryKey: ['reporting-effort-items', selectedEffortId] })
      setBulkEditOpen(false)
      setSelectedRows(new Set())
      setBulkFormData({ item_status: '' })
    } catch (error) {
      toast.error(`Failed to update some items: ${getErrorMessage(error)}`)
    }
  }

  // Filter items by tab
  const filterByTab = (item: ReportingEffortItem) => {
    const subtype = item.item_subtype?.toLowerCase()
    if (activeTab === 'tlf') return ['table', 'listing', 'figure'].includes(subtype || '')
    if (activeTab === 'sdtm') return subtype === 'sdtm'
    if (activeTab === 'adam') return subtype === 'adam'
    return true
  }

  // Filter items by search and tab
  const filteredItems = items
    .filter(filterByTab)
    .filter((item) =>
      item.item_code.toLowerCase().includes(search.toLowerCase()) ||
      (item.item_description?.toLowerCase().includes(search.toLowerCase()) ?? false)
    )

  // Count items per tab
  const tlfCount = items.filter(i => ['table', 'listing', 'figure'].includes(i.item_subtype?.toLowerCase() || '')).length
  const sdtmCount = items.filter(i => i.item_subtype?.toLowerCase() === 'sdtm').length
  const adamCount = items.filter(i => i.item_subtype?.toLowerCase() === 'adam').length

  const selectedEffort = efforts.find((e) => e.id === Number(selectedEffortId))

  if (effortsLoading) {
    return <PageLoader text="Loading reporting efforts..." />
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-primary" />
              Reporting Effort Items
            </CardTitle>
            <CardDescription>
              Manage TLFs and datasets for reporting efforts
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={refetch} disabled={!selectedEffortId}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={() => setCopyDialogOpen(true)} disabled={!selectedEffortId}>
              <Copy className="h-4 w-4 mr-2" />
              Copy Items
            </Button>
            {selectedRows.size > 0 && (
              <Button variant="outline" size="sm" onClick={() => setBulkEditOpen(true)}>
                <CheckSquare className="h-4 w-4 mr-2" />
                Bulk Edit ({selectedRows.size})
              </Button>
            )}
            <Button size="sm" onClick={handleAdd} disabled={!selectedEffortId}>
              <Plus className="h-4 w-4 mr-2" />
              Add Item
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <div className="w-80">
              <Select value={selectedEffortId} onValueChange={(v) => { setSelectedEffortId(v); setSelectedRows(new Set()) }}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a reporting effort" />
                </SelectTrigger>
                <SelectContent>
                  {efforts.map((effort) => (
                    <SelectItem key={effort.id} value={String(effort.id)}>
                      {effort.database_release_label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedEffortId && (
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search items..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
            )}
          </div>

          {!selectedEffortId ? (
            <EmptyState
              icon={ClipboardList}
              title="Select a reporting effort"
              description="Choose a reporting effort to view and manage its items."
            />
          ) : itemsLoading ? (
            <PageLoader text="Loading items..." />
          ) : (
            <Tabs value={activeTab} onValueChange={(v) => { setActiveTab(v as TabType); setSelectedRows(new Set()) }}>
              <TabsList className="mb-4">
                <TabsTrigger value="tlf">
                  TLF Items
                  <Badge variant="secondary" className="ml-2">{tlfCount}</Badge>
                </TabsTrigger>
                <TabsTrigger value="sdtm">
                  SDTM Items
                  <Badge variant="secondary" className="ml-2">{sdtmCount}</Badge>
                </TabsTrigger>
                <TabsTrigger value="adam">
                  ADaM Items
                  <Badge variant="secondary" className="ml-2">{adamCount}</Badge>
                </TabsTrigger>
              </TabsList>

              {['tlf', 'sdtm', 'adam'].map((tab) => (
                <TabsContent key={tab} value={tab}>
                  {filteredItems.length === 0 ? (
                    <EmptyState
                      icon={ClipboardList}
                      title="No items found"
                      description={search ? "Try a different search term." : "Add or copy items to this reporting effort."}
                      action={!search ? { label: 'Add Item', onClick: handleAdd } : undefined}
                    />
                  ) : (
                    <div className="rounded-md border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="w-12">
                              <Checkbox
                                checked={selectedRows.size === filteredItems.length && filteredItems.length > 0}
                                onCheckedChange={handleSelectAll}
                              />
                            </TableHead>
                            <TableHead>Item Code</TableHead>
                            <TableHead>Description</TableHead>
                            <TableHead>Type</TableHead>
                            <TableHead>Subtype</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {filteredItems.map((item) => (
                            <TableRow key={item.id}>
                              <TableCell>
                                <Checkbox
                                  checked={selectedRows.has(item.id)}
                                  onCheckedChange={(checked) => handleSelectRow(item.id, !!checked)}
                                />
                              </TableCell>
                              <TableCell className="font-medium">{item.item_code}</TableCell>
                              <TableCell className="max-w-md truncate">{item.item_description || '-'}</TableCell>
                              <TableCell>
                                <Badge variant={item.item_type === 'TLF' ? 'default' : 'secondary'}>
                                  {item.item_type}
                                </Badge>
                              </TableCell>
                              <TableCell>{item.item_subtype || '-'}</TableCell>
                              <TableCell>
                                <Badge variant={
                                  item.item_status === 'COMPLETED' ? 'success' :
                                  item.item_status === 'IN_PROGRESS' ? 'info' : 'secondary'
                                }>
                                  {item.item_status}
                                </Badge>
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex justify-end gap-1">
                                  <Button variant="ghost" size="icon" onClick={() => handleEdit(item)}>
                                    <Edit className="h-4 w-4" />
                                  </Button>
                                  <Button variant="ghost" size="icon" onClick={() => handleDelete(item)}>
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
                </TabsContent>
              ))}
            </Tabs>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Item Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedItem ? 'Edit Item' : 'Add New Item'}</DialogTitle>
            <DialogDescription>
              {selectedItem ? 'Update item details.' : `Add an item to ${selectedEffort?.database_release_label}.`}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="item_code">Item Code</Label>
              <Input
                id="item_code"
                value={formData.item_code}
                onChange={(e) => setFormData((prev) => ({ ...prev, item_code: e.target.value }))}
                placeholder="e.g., T-14.1.1"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="item_description">Description (Optional)</Label>
              <Input
                id="item_description"
                value={formData.item_description}
                onChange={(e) => setFormData((prev) => ({ ...prev, item_description: e.target.value }))}
                placeholder="Enter description..."
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>Item Type</Label>
                <Select
                  value={formData.item_type}
                  onValueChange={(value: ItemType) => {
                    setFormData((prev) => ({
                      ...prev,
                      item_type: value,
                      item_subtype: value === 'TLF' ? 'Table' : 'SDTM',
                    }))
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ITEM_TYPES.map((type) => (
                      <SelectItem key={type} value={type}>{type}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>Subtype</Label>
                <Select
                  value={formData.item_subtype}
                  onValueChange={(value: ItemSubtype) =>
                    setFormData((prev) => ({ ...prev, item_subtype: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(formData.item_type === 'TLF' ? TLF_SUBTYPES : DATASET_SUBTYPES).map((subtype) => (
                      <SelectItem key={subtype} value={subtype}>{subtype}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={!formData.item_code}>
              {selectedItem ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Copy Items Dialog */}
      <Dialog open={copyDialogOpen} onOpenChange={setCopyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Copy Items</DialogTitle>
            <DialogDescription>
              Copy items from a package or another reporting effort.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Copy From</Label>
              <Select
                value={copySource.type}
                onValueChange={(value: 'package' | 'effort') =>
                  setCopySource({ type: value, id: '' })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="package">Package</SelectItem>
                  <SelectItem value="effort">Reporting Effort</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>Select Source</Label>
              <Select
                value={copySource.id}
                onValueChange={(value) => setCopySource((prev) => ({ ...prev, id: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder={`Select a ${copySource.type}`} />
                </SelectTrigger>
                <SelectContent>
                  {copySource.type === 'package'
                    ? packages.map((pkg) => (
                        <SelectItem key={pkg.id} value={String(pkg.id)}>
                          {pkg.package_name}
                        </SelectItem>
                      ))
                    : efforts
                        .filter((e) => e.id !== Number(selectedEffortId))
                        .map((effort) => (
                          <SelectItem key={effort.id} value={String(effort.id)}>
                            {effort.database_release_label}
                          </SelectItem>
                        ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCopyDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleCopy} disabled={!copySource.id}>
              <Copy className="h-4 w-4 mr-2" />
              Copy Items
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Edit Dialog */}
      <Dialog open={bulkEditOpen} onOpenChange={setBulkEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bulk Edit Items</DialogTitle>
            <DialogDescription>
              Update {selectedRows.size} selected item(s).
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Status</Label>
              <Select
                value={bulkFormData.item_status}
                onValueChange={(value) => setBulkFormData({ item_status: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  {ITEM_STATUSES.map((status) => (
                    <SelectItem key={status} value={status}>{status.replace('_', ' ')}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkEditOpen(false)}>Cancel</Button>
            <Button onClick={handleBulkEdit} disabled={!bulkFormData.item_status}>
              Update {selectedRows.size} Items
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Item?"
        description={`Are you sure you want to delete "${selectedItem?.item_code}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={confirmDelete}
      />
    </div>
  )
}


