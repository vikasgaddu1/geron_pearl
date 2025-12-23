import { useState, useCallback, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Plus, Edit, Trash2, RefreshCw, Upload } from 'lucide-react'
import { toast } from 'sonner'
import { textElementsApi } from '@/api'
import { getErrorMessage } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
import { Badge } from '@/components/ui/badge'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { ExcelUpload, ColumnDefinition } from '@/components/common/ExcelUpload'
import { DataTable, ColumnDef } from '@/components/common/DataTable'
import { TooltipWrapper } from '@/components/common/TooltipWrapper'
import { HelpIcon } from '@/components/common/HelpIcon'
import { useWebSocketRefresh } from '@/hooks/useWebSocket'
import type { TextElement, TextElementType, TextElementFormData } from '@/types'

const TEXT_ELEMENT_TYPES: { value: TextElementType; label: string }[] = [
  { value: 'title', label: 'Titles' },
  { value: 'footnote', label: 'Footnotes' },
  { value: 'population_set', label: 'Population Sets' },
  { value: 'acronyms_set', label: 'Acronyms' },
  { value: 'ich_category', label: 'ICH Categories' },
]

const UPLOAD_COLUMNS: ColumnDefinition[] = [
  { key: 'type', label: 'Type', required: true, validate: (v) => 
    ['title', 'footnote', 'population_set', 'acronyms_set', 'ich_category'].includes(v.toLowerCase()) || 
    'Invalid type (use: title, footnote, population_set, acronyms_set, ich_category)' 
  },
  { key: 'label', label: 'Label', required: true },
  { key: 'content', label: 'Content', required: true },
]

const UPLOAD_SAMPLE_DATA = [
  ['title', 'TITLE_01', 'Summary of Demographics'],
  ['title', 'TITLE_02', 'Adverse Events by System Organ Class'],
  ['footnote', 'FN_01', 'Note: Percentages are based on the Safety Population.'],
  ['footnote', 'FN_02', 'Source: [dataset].'],
  ['population_set', 'SAF', 'Safety Population'],
  ['population_set', 'ITT', 'Intent-to-Treat Population'],
  ['acronyms_set', 'AE', 'Adverse Event'],
  ['acronyms_set', 'SAE', 'Serious Adverse Event'],
  ['ich_category', 'ICH_11.4.2.1', 'ICH E3 Section 11.4.2.1 - Demographic and Baseline Characteristics'],
  ['ich_category', 'ICH_12.2', 'ICH E3 Section 12.2 - Adverse Events'],
]

export function TFLProperties() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<TextElementType>('title')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [selectedElement, setSelectedElement] = useState<TextElement | null>(null)
  const [formData, setFormData] = useState<TextElementFormData>({
    type: 'title',
    label: '',
    content: '',
  })

  // Query
  const { data: elements = [], isLoading } = useQuery({
    queryKey: ['text-elements'],
    queryFn: textElementsApi.getAll,
  })

  // WebSocket refresh
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['text-elements'] })
  }, [queryClient])

  useWebSocketRefresh(['text_element'], refetch)

  // Mutations
  const createElement = useMutation({
    mutationFn: textElementsApi.create,
    onSuccess: () => {
      toast.success('Text element created successfully')
      queryClient.invalidateQueries({ queryKey: ['text-elements'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error) => toast.error(`Failed to create text element: ${getErrorMessage(error)}`),
  })

  const updateElement = useMutation({
    mutationFn: ({ id, data }: { id: number; data: TextElementFormData }) =>
      textElementsApi.update(id, data),
    onSuccess: () => {
      toast.success('Text element updated successfully')
      queryClient.invalidateQueries({ queryKey: ['text-elements'] })
      setDialogOpen(false)
      resetForm()
    },
    onError: (error) => toast.error(`Failed to update text element: ${getErrorMessage(error)}`),
  })

  const deleteElement = useMutation({
    mutationFn: textElementsApi.delete,
    onSuccess: () => {
      toast.success('Text element deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['text-elements'] })
      setSelectedElement(null)
    },
    onError: (error) => toast.error(`Failed to delete text element: ${getErrorMessage(error)}`),
  })

  const resetForm = () => {
    setFormData({ type: activeTab, label: '', content: '' })
    setSelectedElement(null)
  }

  const handleAdd = () => {
    setFormData({ type: activeTab, label: '', content: '' })
    setSelectedElement(null)
    setDialogOpen(true)
  }

  const handleEdit = (element: TextElement) => {
    setSelectedElement(element)
    setFormData({
      type: element.type,
      label: element.label,
      content: element.content,
    })
    setDialogOpen(true)
  }

  const handleDelete = (element: TextElement) => {
    setSelectedElement(element)
    setDeleteDialogOpen(true)
  }

  const handleSubmit = () => {
    if (selectedElement) {
      updateElement.mutate({ id: selectedElement.id, data: formData })
    } else {
      createElement.mutate(formData)
    }
  }

  const confirmDelete = () => {
    if (selectedElement) {
      deleteElement.mutate(selectedElement.id)
      setDeleteDialogOpen(false)
    }
  }

  const handleUpload = async (data: Record<string, string>[]) => {
    let created = 0
    let errors = 0

    for (const row of data) {
      try {
        await textElementsApi.create({
          type: row.type.toLowerCase() as TextElementType,
          label: row.label,
          content: row.content,
        })
        created++
      } catch {
        errors++
      }
    }

    queryClient.invalidateQueries({ queryKey: ['text-elements'] })
    
    if (errors > 0) {
      toast.warning(`Created ${created} elements, ${errors} failed`)
    } else {
      toast.success(`Created ${created} text elements`)
    }
  }

  // Filter elements by type
  const filteredElements = useMemo(
    () => elements.filter((element) => element.type === activeTab),
    [elements, activeTab]
  )

  // Define table columns
  const columns: ColumnDef<TextElement>[] = [
    {
      id: 'label',
      header: 'Label',
      accessorKey: 'label',
      filterType: 'text',
      helpText: 'Unique identifier for this text element. Use wildcards (*) for flexible searching.',
      cell: (value) => <span className="font-medium">{value}</span>,
    },
    {
      id: 'content',
      header: 'Content',
      accessorKey: 'content',
      filterType: 'text',
      helpText: 'The actual text content. Supports wildcard and regex filtering for advanced searches.',
      cell: (value) => <span className="max-w-md truncate block">{value}</span>,
    },
    {
      id: 'actions',
      header: 'Actions',
      accessorKey: 'id',
      filterType: 'none',
      enableSorting: false,
      cell: (_, element) => (
        <div className="flex justify-end gap-2">
          <TooltipWrapper content="Edit text element">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleEdit(element)}
            >
              <Edit className="h-4 w-4" />
            </Button>
          </TooltipWrapper>
          <TooltipWrapper content="Delete text element">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDelete(element)}
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </TooltipWrapper>
        </div>
      ),
    },
  ]

  const getTypeLabel = (type: TextElementType) => {
    return TEXT_ELEMENT_TYPES.find((t) => t.value === type)?.label || type
  }

  const getTypeDescription = (type: TextElementType) => {
    const descriptions = {
      title: 'Standard titles used across TLF outputs',
      footnote: 'Footnotes providing additional context and explanations',
      population_set: 'Analysis population definitions (e.g., Safety, ITT)',
      acronyms_set: 'Abbreviations and their full meanings',
      ich_category: 'ICH E3 guideline section classifications',
    }
    return descriptions[type] || ''
  }

  if (isLoading) {
    return <PageLoader text="Loading text elements..." />
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div className="flex items-center gap-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                TFL Properties
              </CardTitle>
              <CardDescription>
                Manage titles, footnotes, populations, acronyms, and ICH categories
              </CardDescription>
            </div>
            <HelpIcon
              title="TFL Properties"
              content={
                <div className="space-y-2">
                  <p>Text elements are reusable components for TLF outputs:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li><strong>Titles:</strong> Standard output headings</li>
                    <li><strong>Footnotes:</strong> Explanatory notes</li>
                    <li><strong>Populations:</strong> Analysis sets (Safety, ITT)</li>
                    <li><strong>Acronyms:</strong> Abbreviation definitions</li>
                    <li><strong>ICH Categories:</strong> Regulatory classifications</li>
                  </ul>
                </div>
              }
            />
          </div>
          <div className="flex gap-2">
            <TooltipWrapper content="Refresh text elements list">
              <Button variant="outline" size="sm" onClick={refetch}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </TooltipWrapper>
            <TooltipWrapper content="Upload multiple text elements from CSV">
              <Button variant="outline" size="sm" onClick={() => setUploadDialogOpen(true)}>
                <Upload className="h-4 w-4 mr-2" />
                Upload
              </Button>
            </TooltipWrapper>
            <TooltipWrapper content={`Add a new ${getTypeLabel(activeTab).slice(0, -1).toLowerCase()}`}>
              <Button size="sm" onClick={handleAdd}>
                <Plus className="h-4 w-4 mr-2" />
                Add {getTypeLabel(activeTab).slice(0, -1)}
              </Button>
            </TooltipWrapper>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TextElementType)}>
            <TabsList className="mb-4">
              {TEXT_ELEMENT_TYPES.map((type) => (
                <TabsTrigger key={type.value} value={type.value}>
                  {type.label}
                  <Badge variant="secondary" className="ml-2">
                    {elements.filter((e) => e.type === type.value).length}
                  </Badge>
                </TabsTrigger>
              ))}
            </TabsList>

            {TEXT_ELEMENT_TYPES.map((type) => (
              <TabsContent key={type.value} value={type.value}>
                <div className="mb-4 p-3 bg-muted/50 rounded-md flex items-start gap-2">
                  <FileText className="h-4 w-4 mt-0.5 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    {getTypeDescription(type)}
                  </p>
                </div>
                {filteredElements.length === 0 ? (
                  <EmptyState
                    icon={FileText}
                    title={`No ${type.label.toLowerCase()} found`}
                    description={`Get started by adding a ${type.label.slice(0, -1).toLowerCase()}.`}
                    action={{ label: `Add ${type.label.slice(0, -1)}`, onClick: handleAdd }}
                  />
                ) : (
                  <DataTable data={filteredElements} columns={columns} />
                )}
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {selectedElement ? 'Edit' : 'Add'} {getTypeLabel(formData.type).slice(0, -1)}
            </DialogTitle>
            <DialogDescription>
              {selectedElement ? 'Update the text element.' : 'Create a new text element.'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="type">Type</Label>
                <HelpIcon content="Select the category of text element. Type cannot be changed after creation." />
              </div>
              <Select
                value={formData.type}
                onValueChange={(value) => setFormData((prev) => ({ ...prev, type: value as TextElementType }))}
                disabled={!!selectedElement}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TEXT_ELEMENT_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label.slice(0, -1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="label">Label</Label>
                <HelpIcon content="Enter a unique identifier for this text element (e.g., TITLE_01, FN_SAFETY)." />
              </div>
              <Input
                id="label"
                value={formData.label}
                onChange={(e) => setFormData((prev) => ({ ...prev, label: e.target.value }))}
                placeholder="e.g., TITLE_01, FN_SAF, POP_ITT"
              />
            </div>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <Label htmlFor="content">Content</Label>
                <HelpIcon content="Enter the full text that will appear in the TLF output." />
              </div>
              <Textarea
                id="content"
                value={formData.content}
                onChange={(e) => setFormData((prev) => ({ ...prev, content: e.target.value }))}
                placeholder="e.g., Summary of Demographics and Baseline Characteristics"
                rows={5}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!formData.label || !formData.content}>
              {selectedElement ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload Dialog */}
      <ExcelUpload
        open={uploadDialogOpen}
        onOpenChange={setUploadDialogOpen}
        title="Upload TFL Properties"
        description="Upload titles, footnotes, population sets, and acronyms from a CSV file."
        columns={UPLOAD_COLUMNS}
        sampleData={UPLOAD_SAMPLE_DATA}
        templateFilename="tfl_properties_template.csv"
        onUpload={handleUpload}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Text Element?"
        description={`Are you sure you want to delete "${selectedElement?.label}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={confirmDelete}
      />
    </div>
  )
}

