import { useState, useCallback, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ClipboardList, Plus, Edit, Trash2, RefreshCw, Search, Copy, Lock } from 'lucide-react'
import { toast } from 'sonner'
import { reportingEffortsApi, reportingEffortItemsApi, packagesApi, studiesApi, databaseReleasesApi, useIGVersions } from '@/api'
import { useReportingSelectionStore } from '@/stores/reportingSelectionStore'
import { useAuthStore } from '@/stores/authStore'
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
import { TextElementCombobox } from '@/components/common/TextElementCombobox'
import { useWebSocketRefresh } from '@/hooks/useWebSocket'
import type { ReportingEffortItem, ItemType, ItemSubtype, ReportingEffortItemCreateWithDetails } from '@/types'

const ITEM_TYPES: ItemType[] = ['TLF', 'Dataset']
const TLF_SUBTYPES: ItemSubtype[] = ['Table', 'Listing', 'Figure']
const DATASET_SUBTYPES: ItemSubtype[] = ['SDTM', 'ADaM']

type TabType = 'tlf' | 'sdtm' | 'adam'

export function ReportingEffortItems() {
  const queryClient = useQueryClient()
  const { currentUser, isLeadForStudy } = useAuthStore()
  const isGlobalAdmin = currentUser?.is_admin === true
  // Use persisted store for selection state
  const { 
    selectedStudyId, 
    selectedReleaseId, 
    selectedEffortId,
    setSelectedStudyId,
    setSelectedReleaseId,
    setSelectedEffortId 
  } = useReportingSelectionStore()
  const [activeTab, setActiveTab] = useState<TabType>('tlf')
  const [search, setSearch] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [copyDialogOpen, setCopyDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ReportingEffortItem | null>(null)
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())
  const [copySource, setCopySource] = useState<{ type: 'package' | 'effort'; id: string }>({ type: 'package', id: '' })
  const [formData, setFormData] = useState({
    item_code: '',
    item_description: '',
    item_type: 'TLF' as ItemType,
    item_subtype: 'Table' as ItemSubtype,
    ig_version_id: undefined as number | undefined,
    dataset_label: '',  // For SDTM/ADaM items - e.g., "Demographics" for DM
    sorting_order: undefined as number | undefined,  // Run order for datasets
    // TLF properties
    title_id: null as number | null,
    population_flag_id: null as number | null,
    ich_category_id: null as number | null,
    footnote_ids: [] as number[],
    acronym_ids: [] as number[],
  })

  // Fetch IG versions for the form
  const { data: igVersions = [] } = useIGVersions({ active_only: true })

  // Queries
  const { data: allStudies = [] } = useQuery({
    queryKey: ['studies'],
    queryFn: studiesApi.getAll,
  })
  
  // Filter studies for LEAD users - they only see studies where they have LEAD access
  const studies = useMemo(() => {
    if (isGlobalAdmin) return allStudies
    return allStudies.filter(study => isLeadForStudy(study.id))
  }, [allStudies, isGlobalAdmin, isLeadForStudy])

  const { data: allReleases = [] } = useQuery({
    queryKey: ['database-releases'],
    queryFn: databaseReleasesApi.getAll,
  })

  const { data: efforts = [], isLoading: effortsLoading } = useQuery({
    queryKey: ['reporting-efforts'],
    queryFn: reportingEffortsApi.getAll,
  })

  const { data: packages = [] } = useQuery({
    queryKey: ['packages'],
    queryFn: packagesApi.getAll,
  })

  // Filtered data based on cascaded selections
  const filteredReleases = useMemo(() => {
    if (!selectedStudyId) return []
    return allReleases.filter(r => r.study_id === Number(selectedStudyId))
  }, [allReleases, selectedStudyId])

  const filteredEfforts = useMemo(() => {
    if (!selectedReleaseId) return []
    return efforts.filter(e => e.database_release_id === Number(selectedReleaseId))
  }, [efforts, selectedReleaseId])

  const { data: items = [], isLoading: itemsLoading } = useQuery({
    queryKey: ['reporting-effort-items', selectedEffortId],
    queryFn: () => (selectedEffortId ? reportingEffortItemsApi.getByEffortId(Number(selectedEffortId)) : Promise.resolve([])),
    enabled: !!selectedEffortId,
  })

  // Study-scoped permissions for bulk operations
  const { data: studyPermissions } = useQuery({
    queryKey: ['study-permissions', selectedStudyId],
    queryFn: () => studiesApi.getMyPermissions(Number(selectedStudyId)),
    enabled: !!selectedStudyId,
  })

  // Check if current user can perform copy/delete operations
  const canBulkCopy = currentUser?.is_admin || studyPermissions?.can_bulk_copy === true
  const canDeleteItems = currentUser?.is_admin || studyPermissions?.can_delete_items === true

  // Get the selected effort object to check lock status
  const selectedEffort = useMemo(() => {
    if (!selectedEffortId) return null
    return efforts.find(e => e.id === Number(selectedEffortId)) || null
  }, [efforts, selectedEffortId])

  // Check if the selected reporting effort is locked
  const isEffortLocked = selectedEffort?.is_locked === true

  // WebSocket refresh
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['reporting-effort-items', selectedEffortId] })
  }, [queryClient, selectedEffortId])

  useWebSocketRefresh(['reporting_effort_item'], refetch)

  // Mutations
  const createItem = useMutation({
    mutationFn: (data: ReportingEffortItemCreateWithDetails) =>
      reportingEffortItemsApi.createWithDetails(Number(selectedEffortId), data),
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
      ig_version_id: undefined,
      dataset_label: '',
      sorting_order: undefined,
      // Reset TLF properties
      title_id: null,
      population_flag_id: null,
      ich_category_id: null,
      footnote_ids: [],
      acronym_ids: [],
    })
    setSelectedItem(null)
  }

  // Get filtered IG versions based on subtype
  const filteredIGVersions = useMemo(() => {
    if (formData.item_type !== 'Dataset') return []
    const standardType = formData.item_subtype === 'SDTM' ? 'SDTM' : 'ADaM'
    return igVersions.filter(v => v.standard_type === standardType)
  }, [igVersions, formData.item_type, formData.item_subtype])

  // Get latest IG version for each standard type (for default selection)
  const latestIGVersions = useMemo(() => {
    const getLatestVersion = (standardType: 'SDTM' | 'ADaM') => {
      const versions = igVersions.filter(v => v.standard_type === standardType)
      if (versions.length === 0) return undefined
      // Sort by version number descending and get the first one
      return versions.sort((a, b) => {
        const [aMajor, aMinor] = a.version.split('.').map(Number)
        const [bMajor, bMinor] = b.version.split('.').map(Number)
        if (bMajor !== aMajor) return bMajor - aMajor
        return (bMinor || 0) - (aMinor || 0)
      })[0]
    }
    return {
      SDTM: getLatestVersion('SDTM'),
      ADaM: getLatestVersion('ADaM'),
    }
  }, [igVersions])

  const handleAdd = () => {
    resetForm()
    // Set default type based on active tab, with latest IG version for Dataset items
    if (activeTab === 'tlf') {
      setFormData(prev => ({ ...prev, item_type: 'TLF', item_subtype: 'Table', ig_version_id: undefined }))
    } else if (activeTab === 'sdtm') {
      setFormData(prev => ({ ...prev, item_type: 'Dataset', item_subtype: 'SDTM', ig_version_id: latestIGVersions.SDTM?.id }))
    } else {
      setFormData(prev => ({ ...prev, item_type: 'Dataset', item_subtype: 'ADaM', ig_version_id: latestIGVersions.ADaM?.id }))
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
      ig_version_id: item.dataset_details?.ig_version_id,
      dataset_label: item.dataset_details?.label || '',
      sorting_order: item.dataset_details?.sorting_order,
      // Populate TLF details
      title_id: item.tlf_details?.title_id || null,
      population_flag_id: item.tlf_details?.population_flag_id || null,
      ich_category_id: item.tlf_details?.ich_category_id || null,
      footnote_ids: item.footnotes?.map(f => f.footnote_id) || [],
      acronym_ids: item.acronyms?.map(a => a.acronym_id) || [],
    })
    setDialogOpen(true)
  }

  const handleDelete = (item: ReportingEffortItem) => {
    setSelectedItem(item)
    setDeleteDialogOpen(true)
  }

  const handleSubmit = () => {
    const data: ReportingEffortItemCreateWithDetails = {
      reporting_effort_id: Number(selectedEffortId),
      item_code: formData.item_code,
      item_description: formData.item_description || undefined,
      item_type: formData.item_type,
      item_subtype: formData.item_subtype,
    }
    
    // Add TLF details for TLF items
    if (formData.item_type === 'TLF') {
      data.tlf_details = {
        title_id: formData.title_id,
        population_flag_id: formData.population_flag_id,
        ich_category_id: formData.ich_category_id,
      }
      
      // Add footnotes
      if (formData.footnote_ids.length > 0) {
        data.footnotes = formData.footnote_ids.map((id, index) => ({
          footnote_id: id,
          sequence_number: index + 1,
        }))
      }
      
      // Add acronyms
      if (formData.acronym_ids.length > 0) {
        data.acronyms = formData.acronym_ids.map(id => ({
          acronym_id: id,
        }))
      }
    }
    
    // Add dataset_details for Dataset items (label, ig_version_id, sorting_order)
    if (formData.item_type === 'Dataset') {
      const datasetDetails: { label?: string; ig_version_id?: number; sorting_order?: number } = {}
      if (formData.dataset_label) {
        datasetDetails.label = formData.dataset_label
      }
      if (formData.ig_version_id) {
        datasetDetails.ig_version_id = formData.ig_version_id
      }
      if (formData.sorting_order !== undefined) {
        datasetDetails.sorting_order = formData.sorting_order
      }
      if (Object.keys(datasetDetails).length > 0) {
        data.dataset_details = datasetDetails
      }
    }
    
    if (selectedItem) {
      // For update, include all details
      const updateData: Record<string, unknown> = {
        item_code: formData.item_code,
        item_description: formData.item_description,
        item_subtype: formData.item_subtype,
      }
      
      // Include TLF details for TLF items
      if (formData.item_type === 'TLF') {
        updateData.tlf_details = {
          title_id: formData.title_id,
          population_flag_id: formData.population_flag_id,
          ich_category_id: formData.ich_category_id,
        }
        // Include footnotes (even if empty, to clear them)
        updateData.footnotes = formData.footnote_ids.map((id, index) => ({
          footnote_id: id,
          sequence_number: index + 1,
        }))
        // Include acronyms (even if empty, to clear them)
        updateData.acronyms = formData.acronym_ids.map(id => ({
          acronym_id: id,
        }))
      }
      
      // Include dataset details for Dataset items (always include to allow clearing values)
      if (formData.item_type === 'Dataset') {
        updateData.dataset_details = {
          label: formData.dataset_label || null,
          ig_version_id: formData.ig_version_id || null,
          sorting_order: formData.sorting_order ?? null,
        }
      }
      
      updateItem.mutate({ id: selectedItem.id, data: updateData })
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


  // Filter items by tab
  // Memoized filter function
  const filterByTab = useCallback((item: ReportingEffortItem) => {
    const subtype = item.item_subtype?.toLowerCase()
    if (activeTab === 'tlf') return ['table', 'listing', 'figure'].includes(subtype || '')
    if (activeTab === 'sdtm') return subtype === 'sdtm'
    if (activeTab === 'adam') return subtype === 'adam'
    return true
  }, [activeTab])

  // Memoized filtered items - only recalculate when items, activeTab, or search change
  const filteredItems = useMemo(() =>
    items
      .filter(filterByTab)
      .filter((item) =>
        item.item_code.toLowerCase().includes(search.toLowerCase()) ||
        (item.item_description?.toLowerCase().includes(search.toLowerCase()) ?? false)
      ),
    [items, filterByTab, search]
  )

  // Memoized counts per tab - only recalculate when items change
  const { tlfCount, sdtmCount, adamCount } = useMemo(() => ({
    tlfCount: items.filter(i => ['table', 'listing', 'figure'].includes(i.item_subtype?.toLowerCase() || '')).length,
    sdtmCount: items.filter(i => i.item_subtype?.toLowerCase() === 'sdtm').length,
    adamCount: items.filter(i => i.item_subtype?.toLowerCase() === 'adam').length,
  }), [items])

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
              {isEffortLocked && (
                <Badge variant="outline" className="ml-2 gap-1 bg-amber-500/15 text-amber-600 border-amber-500/30">
                  <Lock className="h-3 w-3" />
                  Locked
                </Badge>
              )}
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
            <Button variant="outline" size="sm" onClick={() => setCopyDialogOpen(true)} disabled={!selectedEffortId || !canBulkCopy || isEffortLocked} title={isEffortLocked ? 'Reporting effort is locked' : ''}>
              <Copy className="h-4 w-4 mr-2" />
              Copy Items
            </Button>
            <Button size="sm" onClick={handleAdd} disabled={!selectedEffortId || isEffortLocked} title={isEffortLocked ? 'Reporting effort is locked' : ''}>
              <Plus className="h-4 w-4 mr-2" />
              Add Item
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4 flex-wrap">
            <div className="w-64">
              <Label className="text-sm font-medium mb-1.5 block">Study</Label>
              <Select 
                value={selectedStudyId} 
                onValueChange={(v) => { 
                  setSelectedStudyId(v)
                  setSelectedReleaseId('')
                  setSelectedEffortId('')
                  setSelectedRows(new Set())
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a study" />
                </SelectTrigger>
                <SelectContent>
                  {studies.map((study) => (
                    <SelectItem key={study.id} value={String(study.id)}>
                      {study.study_label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedStudyId && (
              <div className="w-64">
                <Label className="text-sm font-medium mb-1.5 block">Database Release</Label>
                <Select 
                  value={selectedReleaseId} 
                  onValueChange={(v) => { 
                    setSelectedReleaseId(v)
                    setSelectedEffortId('')
                    setSelectedRows(new Set())
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a database release" />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredReleases.map((release) => (
                      <SelectItem key={release.id} value={String(release.id)}>
                        {release.database_release_label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {selectedReleaseId && (
              <div className="w-64">
                <Label className="text-sm font-medium mb-1.5 block">Reporting Effort</Label>
                <Select 
                  value={selectedEffortId} 
                  onValueChange={(v) => { 
                    setSelectedEffortId(v)
                    setSelectedRows(new Set())
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a reporting effort" />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredEfforts.map((effort) => (
                      <SelectItem key={effort.id} value={String(effort.id)}>
                        {effort.database_release_label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {selectedEffortId && (
              <div className="relative flex-1 min-w-64">
                <Label className="text-sm font-medium mb-1.5 block">Search</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search items..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>
            )}
          </div>

          {!selectedStudyId ? (
            <EmptyState
              icon={ClipboardList}
              title="Select a study"
              description="Choose a study to begin filtering reporting efforts."
            />
          ) : !selectedReleaseId ? (
            <EmptyState
              icon={ClipboardList}
              title="Select a database release"
              description="Choose a database release to continue."
            />
          ) : !selectedEffortId ? (
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
                            {(activeTab === 'sdtm' || activeTab === 'adam') && (
                              <TableHead>Label</TableHead>
                            )}
                            {activeTab === 'tlf' && (
                              <TableHead>Title</TableHead>
                            )}
                            <TableHead>Type</TableHead>
                            <TableHead>Subtype</TableHead>
                            {(activeTab === 'sdtm' || activeTab === 'adam') && (
                              <TableHead>IG Version</TableHead>
                            )}
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
                              {(activeTab === 'sdtm' || activeTab === 'adam') && (
                                <TableCell className="max-w-xs truncate">
                                  {item.dataset_details?.label || '-'}
                                </TableCell>
                              )}
                              {activeTab === 'tlf' && (
                                <TableCell className="max-w-md truncate">
                                  {item.tlf_details?.title?.content || item.tlf_details?.title?.label || item.item_description || '-'}
                                </TableCell>
                              )}
                              <TableCell>
                                <Badge variant={item.item_type === 'TLF' ? 'default' : 'secondary'}>
                                  {item.item_type}
                                </Badge>
                              </TableCell>
                              <TableCell>{item.item_subtype || '-'}</TableCell>
                              {(activeTab === 'sdtm' || activeTab === 'adam') && (
                                <TableCell>
                                  {item.dataset_details?.ig_version ? (
                                    <Badge variant="outline">
                                      v{item.dataset_details.ig_version.version}
                                    </Badge>
                                  ) : (
                                    <span className="text-muted-foreground">-</span>
                                  )}
                                </TableCell>
                              )}
                              <TableCell className="text-right">
                                <div className="flex justify-end gap-1">
                                  <Button variant="ghost" size="icon" onClick={() => handleEdit(item)} disabled={isEffortLocked} title={isEffortLocked ? 'Reporting effort is locked' : ''}>
                                    <Edit className="h-4 w-4" />
                                  </Button>
                                  {canDeleteItems && (
                                    <Button variant="ghost" size="icon" onClick={() => handleDelete(item)} disabled={isEffortLocked} title={isEffortLocked ? 'Reporting effort is locked' : ''}>
                                      <Trash2 className="h-4 w-4 text-destructive" />
                                    </Button>
                                  )}
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
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedItem 
                ? `Edit ${formData.item_type === 'TLF' ? 'TLF Report' : 'Dataset'}` 
                : `Add New ${formData.item_type === 'TLF' ? 'TLF Report' : 'Dataset'}`}
            </DialogTitle>
            <DialogDescription>
              {selectedItem 
                ? 'Update item details.' 
                : `Add a new ${formData.item_type === 'TLF' ? 'TLF report' : 'dataset'} to ${selectedEffort?.database_release_label}.`}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {/* Row 1: Item Type selector */}
            <div className="grid gap-2">
              <Label>Item Type</Label>
              <Select
                value={formData.item_type}
                onValueChange={(value: ItemType) => {
                  setFormData((prev) => ({
                    ...prev,
                    item_type: value,
                    item_subtype: value === 'TLF' ? 'Table' : 'SDTM',
                    item_description: '', // Clear description when switching
                    ig_version_id: value === 'Dataset' ? latestIGVersions.SDTM?.id : undefined,
                  }))
                }}
              >
                <SelectTrigger className="w-[200px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ITEM_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>{type}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* TLF Form - matches Package Items layout */}
            {formData.item_type === 'TLF' && (
              <>
                {/* Row 2: TLF Type and Item Code */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>TLF Type *</Label>
                    <Select
                      value={formData.item_subtype}
                      onValueChange={(value: ItemSubtype) => {
                        setFormData((prev) => ({ ...prev, item_subtype: value }))
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TLF_SUBTYPES.map((subtype) => (
                          <SelectItem key={subtype} value={subtype}>{subtype}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="item_code">Title Key / Code *</Label>
                    <Input
                      id="item_code"
                      value={formData.item_code}
                      onChange={(e) => setFormData((prev) => ({ ...prev, item_code: e.target.value }))}
                      placeholder="e.g., t14.1.1"
                    />
                  </div>
                </div>
                
                {/* Row 3: Title */}
                <div className="grid gap-2">
                  <Label>Title</Label>
                  <TextElementCombobox
                    type="title"
                    value={formData.title_id}
                    onChange={(id) => setFormData((prev) => ({ ...prev, title_id: id }))}
                    placeholder="Search or create title..."
                  />
                </div>
                
                {/* Row 4: Population Flag and ICH Category */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>Population Flag</Label>
                    <TextElementCombobox
                      type="population_set"
                      value={formData.population_flag_id}
                      onChange={(id) => setFormData((prev) => ({ ...prev, population_flag_id: id }))}
                      placeholder="Search or create population..."
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>ICH Category</Label>
                    <TextElementCombobox
                      type="ich_category"
                      value={formData.ich_category_id}
                      onChange={(id) => setFormData((prev) => ({ ...prev, ich_category_id: id }))}
                      placeholder="Search or create ICH category..."
                    />
                  </div>
                </div>
                
                {/* Row 5: Footnotes */}
                <div className="grid gap-2">
                  <Label>Footnotes</Label>
                  <TextElementCombobox
                    type="footnote"
                    values={formData.footnote_ids}
                    onMultiChange={(ids) => setFormData((prev) => ({ ...prev, footnote_ids: ids }))}
                    multiple
                    placeholder="Search or create footnotes..."
                  />
                </div>
                
                {/* Row 6: Acronyms */}
                <div className="grid gap-2">
                  <Label>Acronyms</Label>
                  <TextElementCombobox
                    type="acronyms_set"
                    values={formData.acronym_ids}
                    onMultiChange={(ids) => setFormData((prev) => ({ ...prev, acronym_ids: ids }))}
                    multiple
                    placeholder="Search or create acronyms..."
                  />
                </div>
              </>
            )}
            
            {/* Dataset Form */}
            {formData.item_type === 'Dataset' && (
              <>
                {/* Row 2: Dataset Type and Item Code */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>Dataset Type *</Label>
                    <Select
                      value={formData.item_subtype}
                      onValueChange={(value: ItemSubtype) => {
                        const newIGVersionId = value === 'SDTM' ? latestIGVersions.SDTM?.id : latestIGVersions.ADaM?.id
                        setFormData((prev) => ({ ...prev, item_subtype: value, ig_version_id: newIGVersionId }))
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {DATASET_SUBTYPES.map((subtype) => (
                          <SelectItem key={subtype} value={subtype}>{subtype}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="item_code">Dataset Name *</Label>
                    <Input
                      id="item_code"
                      value={formData.item_code}
                      onChange={(e) => setFormData((prev) => ({ ...prev, item_code: e.target.value.toUpperCase() }))}
                      placeholder="e.g., DM, AE, ADSL"
                    />
                  </div>
                </div>

                {/* Row 3: Dataset Label */}
                <div className="grid gap-2">
                  <Label htmlFor="dataset_label">Dataset Label</Label>
                  <Input
                    id="dataset_label"
                    value={formData.dataset_label}
                    onChange={(e) => setFormData((prev) => ({ ...prev, dataset_label: e.target.value }))}
                    placeholder="e.g., Demographics, Adverse Events"
                  />
                  <p className="text-xs text-muted-foreground">
                    Descriptive name for the dataset (shown in dashboards)
                  </p>
                </div>

                {/* Row 4: IG Version */}
                {filteredIGVersions.length > 0 && (
                  <div className="grid gap-2">
                    <Label>IG Version</Label>
                    <Select
                      value={formData.ig_version_id?.toString() || '__none__'}
                      onValueChange={(value) =>
                        setFormData((prev) => ({ 
                          ...prev, 
                          ig_version_id: value === '__none__' ? undefined : parseInt(value) 
                        }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select IG version" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="__none__">None</SelectItem>
                        {filteredIGVersions.map((version) => (
                          <SelectItem key={version.id} value={String(version.id)}>
                            v{version.version} {version.description && `- ${version.description}`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      {formData.item_subtype} Implementation Guide version
                    </p>
                  </div>
                )}

                {/* Row 5: Run Order */}
                <div className="grid gap-2">
                  <Label htmlFor="sorting_order">Run Order</Label>
                  <Input
                    id="sorting_order"
                    type="number"
                    min={1}
                    value={formData.sorting_order || ''}
                    onChange={(e) => setFormData((prev) => ({ 
                      ...prev, 
                      sorting_order: e.target.value ? parseInt(e.target.value) : undefined 
                    }))}
                    placeholder="Display order (1, 2, 3...)"
                  />
                  <p className="text-xs text-muted-foreground">
                    Order in which dataset programs should be run
                  </p>
                </div>
              </>
            )}
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


