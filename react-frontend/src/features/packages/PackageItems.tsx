import { useState, useCallback, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { PackageOpen, Plus, Edit, Trash2, RefreshCw, Search, Upload, Download, CheckSquare, Loader2, FileSpreadsheet } from 'lucide-react'
import { toast } from 'sonner'
import { packagesApi, textElementsApi } from '@/api'
import type { BulkTLFItem, BulkDatasetItem } from '@/api/endpoints/packages'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
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
import type { PackageItem, TextElement } from '@/types'
import { TLFItemForm, TLFFormData } from './TLFItemForm'
import { DatasetItemForm, DatasetFormData } from './DatasetItemForm'

type TabType = 'tlf' | 'sdtm' | 'adam'

export function PackageItems() {
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<TabType>('tlf')
  const [search, setSearch] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<PackageItem | null>(null)
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())

  // Form data for TLF and Dataset
  const [tlfFormData, setTlfFormData] = useState<TLFFormData>({
    item_subtype: 'Table',
    item_code: '',
    title_id: null,
    population_flag_id: null,
    ich_category_id: null,
    footnote_ids: [],
    acronym_ids: [],
  })

  const [datasetFormData, setDatasetFormData] = useState<DatasetFormData>({
    item_subtype: 'SDTM',
    item_code: '',
    label: '',
    sorting_order: undefined,
  })

  // Upload state
  const [uploadTab, setUploadTab] = useState<'tlf' | 'dataset'>('tlf')
  const [uploadData, setUploadData] = useState<{
    file: File | null
    tlfItems: BulkTLFItem[]
    datasetItems: BulkDatasetItem[]
  }>({
    file: null,
    tlfItems: [],
    datasetItems: [],
  })
  const [uploading, setUploading] = useState(false)

  const selectedPackageId = searchParams.get('package')

  // Queries
  const { data: packages = [], isLoading: packagesLoading } = useQuery({
    queryKey: ['packages'],
    queryFn: packagesApi.getAll,
  })

  const { data: items = [], isLoading: itemsLoading } = useQuery({
    queryKey: ['package-items', selectedPackageId],
    queryFn: () => (selectedPackageId ? packagesApi.getItems(Number(selectedPackageId)) : Promise.resolve([])),
    enabled: !!selectedPackageId,
  })

  // Fetch all text elements for display resolution
  const { data: textElements = [] } = useQuery({
    queryKey: ['text-elements'],
    queryFn: textElementsApi.getAll,
  })

  // Create lookup map for text elements
  const textElementMap = useMemo(() => {
    const map = new Map<number, TextElement>()
    textElements.forEach(el => map.set(el.id, el))
    return map
  }, [textElements])

  // Helper to resolve text element ID to label
  const resolveTextElement = (id?: number | null): string => {
    if (!id) return '-'
    const element = textElementMap.get(id)
    return element?.label || '-'
  }

  // WebSocket refresh
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['package-items', selectedPackageId] })
    queryClient.invalidateQueries({ queryKey: ['text-elements'] })
  }, [queryClient, selectedPackageId])

  useWebSocketRefresh(['package_item', 'text_element'], refetch)

  // Mutations
  const createItem = useMutation({
    mutationFn: (data: Parameters<typeof packagesApi.createItemWithDetails>[1]) =>
      packagesApi.createItemWithDetails(Number(selectedPackageId), data),
    onSuccess: () => {
      toast.success('Package item created successfully')
      queryClient.invalidateQueries({ queryKey: ['package-items', selectedPackageId] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to create package item'),
  })

  const updateItem = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Parameters<typeof packagesApi.updateItemWithDetails>[1] }) =>
      packagesApi.updateItemWithDetails(id, data),
    onSuccess: () => {
      toast.success('Package item updated successfully')
      queryClient.invalidateQueries({ queryKey: ['package-items', selectedPackageId] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to update package item'),
  })

  const deleteItem = useMutation({
    mutationFn: packagesApi.deleteItem,
    onSuccess: () => {
      toast.success('Package item deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['package-items', selectedPackageId] })
      setSelectedItem(null)
    },
    onError: () => toast.error('Failed to delete package item'),
  })

  // Bulk upload mutations
  const bulkCreateTLF = useMutation({
    mutationFn: (items: BulkTLFItem[]) =>
      packagesApi.bulkCreateTLFItems(Number(selectedPackageId), items),
    onSuccess: (result) => {
      if (result.success) {
        toast.success(`Created ${result.created_count} TLF items`)
      } else {
        toast.warning(`Created ${result.created_count} items with ${result.errors.length} errors`)
        result.errors.forEach(err => toast.error(err))
      }
      queryClient.invalidateQueries({ queryKey: ['package-items', selectedPackageId] })
      setUploadDialogOpen(false)
      resetUploadData()
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to upload items'),
  })

  const bulkCreateDataset = useMutation({
    mutationFn: (items: BulkDatasetItem[]) =>
      packagesApi.bulkCreateDatasetItems(Number(selectedPackageId), items),
    onSuccess: (result) => {
      if (result.success) {
        toast.success(`Created ${result.created_count} dataset items`)
      } else {
        toast.warning(`Created ${result.created_count} items with ${result.errors.length} errors`)
        result.errors.forEach(err => toast.error(err))
      }
      queryClient.invalidateQueries({ queryKey: ['package-items', selectedPackageId] })
      setUploadDialogOpen(false)
      resetUploadData()
    },
    onError: (error: Error) => toast.error(error.message || 'Failed to upload items'),
  })

  const resetForm = () => {
    setTlfFormData({
      item_subtype: 'Table',
      item_code: '',
      title_id: null,
      population_flag_id: null,
      ich_category_id: null,
      footnote_ids: [],
      acronym_ids: [],
    })
    setDatasetFormData({
      item_subtype: 'SDTM',
      item_code: '',
      label: '',
      sorting_order: undefined,
    })
    setSelectedItem(null)
  }

  const resetUploadData = () => {
    setUploadData({ file: null, tlfItems: [], datasetItems: [] })
  }

  const handlePackageChange = (packageId: string) => {
    setSearchParams({ package: packageId })
    setSelectedRows(new Set())
  }

  const handleAdd = () => {
    resetForm()
    // Set default type based on active tab
    if (activeTab === 'tlf') {
      setTlfFormData(prev => ({ ...prev, item_subtype: 'Table' }))
    } else if (activeTab === 'sdtm') {
      setDatasetFormData(prev => ({ ...prev, item_subtype: 'SDTM' }))
    } else {
      setDatasetFormData(prev => ({ ...prev, item_subtype: 'ADaM' }))
    }
    setDialogOpen(true)
  }

  const handleEdit = (item: PackageItem) => {
    setSelectedItem(item)
    if (item.item_type === 'TLF') {
      setTlfFormData({
        item_subtype: item.item_subtype || 'Table',
        item_code: item.item_code,
        title_id: item.tlf_details?.title_id || null,
        population_flag_id: item.tlf_details?.population_flag_id || null,
        ich_category_id: item.tlf_details?.ich_category_id || null,
        footnote_ids: item.footnotes?.map(f => f.footnote_id) || [],
        acronym_ids: item.acronyms?.map(a => a.acronym_id) || [],
      })
    } else {
      setDatasetFormData({
        item_subtype: item.item_subtype || 'SDTM',
        item_code: item.item_code,
        label: item.dataset_details?.label || '',
        sorting_order: item.dataset_details?.sorting_order,
      })
    }
    setDialogOpen(true)
  }

  const handleDelete = (item: PackageItem) => {
    setSelectedItem(item)
    setDeleteDialogOpen(true)
  }

  const handleSubmit = () => {
    const isTLF = activeTab === 'tlf' || (selectedItem && selectedItem.item_type === 'TLF')

    if (isTLF) {
      if (!tlfFormData.item_code || !tlfFormData.item_subtype) {
        toast.error('Please fill in required fields')
        return
      }

      const data = {
        package_id: Number(selectedPackageId),
        item_type: 'TLF' as const,
        item_subtype: tlfFormData.item_subtype,
        item_code: tlfFormData.item_code,
        tlf_details: {
          title_id: tlfFormData.title_id || undefined,
          population_flag_id: tlfFormData.population_flag_id || undefined,
          ich_category_id: tlfFormData.ich_category_id || undefined,
        },
        footnotes: tlfFormData.footnote_ids?.map((id, idx) => ({ footnote_id: id, sequence_number: idx + 1 })) || [],
        acronyms: tlfFormData.acronym_ids?.map(id => ({ acronym_id: id })) || [],
      }

      if (selectedItem) {
        updateItem.mutate({ id: selectedItem.id, data })
      } else {
        createItem.mutate(data)
      }
    } else {
      if (!datasetFormData.item_code || !datasetFormData.item_subtype) {
        toast.error('Please fill in required fields')
        return
      }

      const data = {
        package_id: Number(selectedPackageId),
        item_type: 'Dataset' as const,
        item_subtype: datasetFormData.item_subtype,
        item_code: datasetFormData.item_code,
        dataset_details: {
          label: datasetFormData.label || undefined,
          sorting_order: datasetFormData.sorting_order,
        },
        footnotes: [],
        acronyms: [],
      }

      if (selectedItem) {
        updateItem.mutate({ id: selectedItem.id, data })
      } else {
        createItem.mutate(data)
      }
    }
  }

  const confirmDelete = () => {
    if (selectedItem) {
      deleteItem.mutate(selectedItem.id)
      setDeleteDialogOpen(false)
    }
  }

  // Select handlers
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

  // Template download handlers
  const downloadTLFTemplate = () => {
    const headers = ['item_code', 'item_subtype', 'title', 'population_flag', 'ich_category']
    const sampleData = [
      ['t14.1.1', 'Table', 'Summary of Demographics', 'Safety Population', 'Efficacy'],
      ['l16.2.1', 'Listing', 'Subject Disposition', 'ITT Population', ''],
      ['f14.1', 'Figure', 'Kaplan-Meier Plot', 'Safety Population', 'Safety'],
    ]

    const csvContent = [headers.join(','), ...sampleData.map(row => row.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tlf_items_template.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadDatasetTemplate = () => {
    const headers = ['item_code', 'item_subtype', 'label', 'sorting_order']
    const sampleData = [
      ['DM', 'SDTM', 'Demographics', '1'],
      ['AE', 'SDTM', 'Adverse Events', '2'],
      ['ADSL', 'ADaM', 'Subject Level Analysis Dataset', '1'],
      ['ADAE', 'ADaM', 'Adverse Events Analysis Dataset', '2'],
    ]

    const csvContent = [headers.join(','), ...sampleData.map(row => row.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'dataset_items_template.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target?.result as string
      const lines = text.split('\n').filter(line => line.trim())
      const headers = lines[0].split(',').map(h => h.trim().toLowerCase())

      if (uploadTab === 'tlf') {
        const data: BulkTLFItem[] = lines.slice(1).map(line => {
          const values = line.split(',').map(v => v.trim())
          const row: Record<string, string> = {}
          headers.forEach((header, index) => {
            row[header] = values[index] || ''
          })
          return {
            item_code: row.item_code || '',
            item_subtype: row.item_subtype || 'Table',
            title: row.title || '',
            population_flag: row.population_flag || undefined,
            ich_category: row.ich_category || undefined,
            footnotes: row.footnotes ? row.footnotes.split(';').filter(Boolean) : [],
            acronyms: row.acronyms ? row.acronyms.split(';').filter(Boolean) : [],
          }
        }).filter(item => item.item_code)
        setUploadData({ file, tlfItems: data, datasetItems: [] })
      } else {
        const data: BulkDatasetItem[] = lines.slice(1).map(line => {
          const values = line.split(',').map(v => v.trim())
          const row: Record<string, string> = {}
          headers.forEach((header, index) => {
            row[header] = values[index] || ''
          })
          return {
            item_code: row.item_code || '',
            item_subtype: row.item_subtype || 'SDTM',
            label: row.label || undefined,
            sorting_order: row.sorting_order ? parseInt(row.sorting_order) : undefined,
          }
        }).filter(item => item.item_code)
        setUploadData({ file, tlfItems: [], datasetItems: data })
      }
    }
    reader.readAsText(file)
  }

  const handleUpload = () => {
    setUploading(true)
    if (uploadTab === 'tlf' && uploadData.tlfItems.length > 0) {
      bulkCreateTLF.mutate(uploadData.tlfItems)
    } else if (uploadTab === 'dataset' && uploadData.datasetItems.length > 0) {
      bulkCreateDataset.mutate(uploadData.datasetItems)
    }
    setUploading(false)
  }

  // Filter items by tab
  const filterByTab = (item: PackageItem) => {
    const subtype = item.item_subtype?.toLowerCase()
    if (activeTab === 'tlf') return ['table', 'listing', 'figure'].includes(subtype || '')
    if (activeTab === 'sdtm') return subtype === 'sdtm'
    if (activeTab === 'adam') return subtype === 'adam'
    return true
  }

  // Filter items
  const filteredItems = items
    .filter(filterByTab)
    .filter((item) =>
      item.item_code.toLowerCase().includes(search.toLowerCase()) ||
      (item.item_description?.toLowerCase().includes(search.toLowerCase()) ?? false) ||
      (resolveTextElement(item.tlf_details?.title_id).toLowerCase().includes(search.toLowerCase()))
    )

  // Count items per tab
  const tlfCount = items.filter(i => ['table', 'listing', 'figure'].includes(i.item_subtype?.toLowerCase() || '')).length
  const sdtmCount = items.filter(i => i.item_subtype?.toLowerCase() === 'sdtm').length
  const adamCount = items.filter(i => i.item_subtype?.toLowerCase() === 'adam').length

  const selectedPackage = packages.find((p) => p.id === Number(selectedPackageId))

  const isTLFForm = activeTab === 'tlf' || (selectedItem && selectedItem.item_type === 'TLF')

  if (packagesLoading) {
    return <PageLoader text="Loading packages..." />
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <PackageOpen className="h-5 w-5 text-primary" />
              Package Items
            </CardTitle>
            <CardDescription>
              Manage TLF reports and datasets within template packages
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={refetch} disabled={!selectedPackageId}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={() => setUploadDialogOpen(true)} disabled={!selectedPackageId}>
              <Upload className="h-4 w-4 mr-2" />
              Bulk Upload
            </Button>
            {selectedRows.size > 0 && (
              <Button variant="outline" size="sm" onClick={() => {
                const selectedItems = filteredItems.filter(i => selectedRows.has(i.id))
                const selectedIds = selectedItems.map(i => i.id)
                toast.info(`${selectedIds.length} items selected`)
              }}>
                <CheckSquare className="h-4 w-4 mr-2" />
                Selected ({selectedRows.size})
              </Button>
            )}
            <Button size="sm" onClick={handleAdd} disabled={!selectedPackageId}>
              <Plus className="h-4 w-4 mr-2" />
              Add Item
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <div className="w-64">
              <Select
                value={selectedPackageId || 'none'}
                onValueChange={(v) => v !== 'none' && handlePackageChange(v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a package" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none" disabled>Select a package</SelectItem>
                  {packages.map((pkg) => (
                    <SelectItem key={pkg.id} value={String(pkg.id)}>
                      {pkg.package_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedPackageId && (
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

          {!selectedPackageId ? (
            <EmptyState
              icon={PackageOpen}
              title="Select a package"
              description="Choose a package from the dropdown to view its items."
            />
          ) : itemsLoading ? (
            <PageLoader text="Loading items..." />
          ) : (
            <Tabs value={activeTab} onValueChange={(v) => { setActiveTab(v as TabType); setSelectedRows(new Set()) }}>
              <TabsList className="mb-4">
                <TabsTrigger value="tlf">
                  TLF Reports
                  <Badge variant="secondary" className="ml-2">{tlfCount}</Badge>
                </TabsTrigger>
                <TabsTrigger value="sdtm">
                  SDTM Datasets
                  <Badge variant="secondary" className="ml-2">{sdtmCount}</Badge>
                </TabsTrigger>
                <TabsTrigger value="adam">
                  ADaM Datasets
                  <Badge variant="secondary" className="ml-2">{adamCount}</Badge>
                </TabsTrigger>
              </TabsList>

              {/* TLF Tab */}
              <TabsContent value="tlf">
                {filteredItems.length === 0 ? (
                  <EmptyState
                    icon={PackageOpen}
                    title="No TLF items found"
                    description={search ? "Try a different search term." : `Add TLF reports to ${selectedPackage?.package_name}.`}
                    action={!search ? { label: 'Add TLF Item', onClick: handleAdd } : undefined}
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
                          <TableHead>Type</TableHead>
                          <TableHead>Title Key</TableHead>
                          <TableHead>Title</TableHead>
                          <TableHead>Population</TableHead>
                          <TableHead>ICH Category</TableHead>
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
                            <TableCell>
                              <Badge variant="outline">{item.item_subtype}</Badge>
                            </TableCell>
                            <TableCell className="font-medium">{item.item_code}</TableCell>
                            <TableCell className="max-w-xs truncate">
                              {resolveTextElement(item.tlf_details?.title_id)}
                            </TableCell>
                            <TableCell>
                              {resolveTextElement(item.tlf_details?.population_flag_id)}
                            </TableCell>
                            <TableCell>
                              {resolveTextElement(item.tlf_details?.ich_category_id)}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
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

              {/* SDTM Tab */}
              <TabsContent value="sdtm">
                {filteredItems.length === 0 ? (
                  <EmptyState
                    icon={PackageOpen}
                    title="No SDTM datasets found"
                    description={search ? "Try a different search term." : `Add SDTM datasets to ${selectedPackage?.package_name}.`}
                    action={!search ? { label: 'Add SDTM Dataset', onClick: handleAdd } : undefined}
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
                          <TableHead>Dataset Name</TableHead>
                          <TableHead>Label</TableHead>
                          <TableHead>Run Order</TableHead>
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
                            <TableCell className="max-w-xs truncate">
                              {item.dataset_details?.label || '-'}
                            </TableCell>
                            <TableCell>
                              {item.dataset_details?.sorting_order || '-'}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
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

              {/* ADaM Tab */}
              <TabsContent value="adam">
                {filteredItems.length === 0 ? (
                  <EmptyState
                    icon={PackageOpen}
                    title="No ADaM datasets found"
                    description={search ? "Try a different search term." : `Add ADaM datasets to ${selectedPackage?.package_name}.`}
                    action={!search ? { label: 'Add ADaM Dataset', onClick: handleAdd } : undefined}
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
                          <TableHead>Dataset Name</TableHead>
                          <TableHead>Label</TableHead>
                          <TableHead>Run Order</TableHead>
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
                            <TableCell className="max-w-xs truncate">
                              {item.dataset_details?.label || '-'}
                            </TableCell>
                            <TableCell>
                              {item.dataset_details?.sorting_order || '-'}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-2">
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
            </Tabs>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>
              {selectedItem ? 'Edit Item' : `Add New ${isTLFForm ? 'TLF Report' : 'Dataset'}`}
            </DialogTitle>
            <DialogDescription>
              {selectedItem ? 'Update item details.' : `Add a new ${isTLFForm ? 'TLF report' : 'dataset'} to the package.`}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            {isTLFForm ? (
              <TLFItemForm
                data={tlfFormData}
                onChange={setTlfFormData}
              />
            ) : (
              <DatasetItemForm
                data={datasetFormData}
                onChange={setDatasetFormData}
              />
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={createItem.isPending || updateItem.isPending}
            >
              {(createItem.isPending || updateItem.isPending) && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              {selectedItem ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5" />
              Bulk Upload Package Items
            </DialogTitle>
            <DialogDescription>
              Upload items from a CSV file. Download the appropriate template for the correct format.
            </DialogDescription>
          </DialogHeader>

          <Tabs value={uploadTab} onValueChange={(v) => { setUploadTab(v as 'tlf' | 'dataset'); resetUploadData() }}>
            <TabsList className="mb-4">
              <TabsTrigger value="tlf">TLF Reports</TabsTrigger>
              <TabsTrigger value="dataset">Datasets</TabsTrigger>
            </TabsList>

            <TabsContent value="tlf" className="space-y-4">
              <div className="flex items-center gap-4">
                <Button variant="outline" onClick={downloadTLFTemplate}>
                  <Download className="h-4 w-4 mr-2" />
                  Download TLF Template
                </Button>
                <div className="flex-1">
                  <Input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    key={uploadTab} // Reset input when tab changes
                  />
                </div>
              </div>

              {uploadData.tlfItems.length > 0 && (
                <div className="rounded-md border max-h-64 overflow-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Title Key</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Title</TableHead>
                        <TableHead>Population</TableHead>
                        <TableHead>ICH Category</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {uploadData.tlfItems.slice(0, 10).map((row, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{row.item_code}</TableCell>
                          <TableCell>{row.item_subtype}</TableCell>
                          <TableCell className="max-w-xs truncate">{row.title}</TableCell>
                          <TableCell>{row.population_flag || '-'}</TableCell>
                          <TableCell>{row.ich_category || '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  {uploadData.tlfItems.length > 10 && (
                    <p className="p-2 text-center text-sm text-muted-foreground">
                      ...and {uploadData.tlfItems.length - 10} more rows
                    </p>
                  )}
                </div>
              )}
            </TabsContent>

            <TabsContent value="dataset" className="space-y-4">
              <div className="flex items-center gap-4">
                <Button variant="outline" onClick={downloadDatasetTemplate}>
                  <Download className="h-4 w-4 mr-2" />
                  Download Dataset Template
                </Button>
                <div className="flex-1">
                  <Input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    key={uploadTab}
                  />
                </div>
              </div>

              {uploadData.datasetItems.length > 0 && (
                <div className="rounded-md border max-h-64 overflow-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Dataset Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Label</TableHead>
                        <TableHead>Run Order</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {uploadData.datasetItems.slice(0, 10).map((row, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{row.item_code}</TableCell>
                          <TableCell>{row.item_subtype}</TableCell>
                          <TableCell className="max-w-xs truncate">{row.label || '-'}</TableCell>
                          <TableCell>{row.sorting_order || '-'}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  {uploadData.datasetItems.length > 10 && (
                    <p className="p-2 text-center text-sm text-muted-foreground">
                      ...and {uploadData.datasetItems.length - 10} more rows
                    </p>
                  )}
                </div>
              )}
            </TabsContent>
          </Tabs>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setUploadDialogOpen(false); resetUploadData() }}>
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={
                uploading ||
                (uploadTab === 'tlf' && uploadData.tlfItems.length === 0) ||
                (uploadTab === 'dataset' && uploadData.datasetItems.length === 0)
              }
            >
              {uploading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              <Upload className="h-4 w-4 mr-2" />
              Upload {uploadTab === 'tlf' ? uploadData.tlfItems.length : uploadData.datasetItems.length} Items
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

