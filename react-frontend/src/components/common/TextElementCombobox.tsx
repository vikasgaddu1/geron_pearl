import { useState, useRef, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, X, Plus, Loader2, ChevronDown } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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
import { cn } from '@/lib/utils'
import { textElementsApi } from '@/api'
import type { TextElement, TextElementType } from '@/types'

// Field labels for each text element type
const TYPE_FIELD_CONFIG: Record<TextElementType, {
  labelField: string
  contentField: string
  labelPlaceholder: string
  contentPlaceholder: string
  labelHelp: string
  contentHelp: string
}> = {
  title: {
    labelField: 'Category',
    contentField: 'Title Text',
    labelPlaceholder: 'e.g., Safety, Efficacy, General',
    contentPlaceholder: 'e.g., Summary of Demographics and Baseline Characteristics',
    labelHelp: 'Category to group similar titles',
    contentHelp: 'The actual title text'
  },
  footnote: {
    labelField: 'Category',
    contentField: 'Footnote Text',
    labelPlaceholder: 'e.g., Safety, Efficacy, General',
    contentPlaceholder: 'e.g., Percentages are based on the number of subjects...',
    labelHelp: 'Category to group similar footnotes',
    contentHelp: 'The actual footnote text'
  },
  population_set: {
    labelField: 'Short Form',
    contentField: 'Full Name',
    labelPlaceholder: 'e.g., SAFFL, ITTFL, PP',
    contentPlaceholder: 'e.g., Safety Analysis Population',
    labelHelp: 'Short form or ADaM variable name',
    contentHelp: 'Full descriptive name'
  },
  acronyms_set: {
    labelField: 'Abbreviation',
    contentField: 'Full Form',
    labelPlaceholder: 'e.g., AE, SAE, SD',
    contentPlaceholder: 'e.g., Adverse Event',
    labelHelp: 'The abbreviated form',
    contentHelp: 'The full expanded form'
  },
  ich_category: {
    labelField: 'ICH Code',
    contentField: 'Description',
    labelPlaceholder: 'e.g., 11.4, 12.1',
    contentPlaceholder: 'e.g., Efficacy Results',
    labelHelp: 'ICH E3 section code',
    contentHelp: 'Description of the category'
  }
}

// Display format helpers for different text element types
const getDisplayText = (element: TextElement, type: TextElementType): string => {
  const { label, content } = element
  
  switch (type) {
    case 'title':
    case 'footnote':
      // Show "Category: Content" for titles/footnotes if both exist
      // If no content, the label IS the content (legacy/inline created)
      if (content) {
        return `${label}: ${content}`
      }
      return label
    case 'population_set':
      // Show "ShortForm - Full Name" for population sets
      return content ? `${label} - ${content}` : label
    case 'acronyms_set':
      // Show "Abbreviation - Full Form" for acronyms
      return content ? `${label} - ${content}` : label
    case 'ich_category':
      // Show "Code - Description" for ICH categories
      return content ? `${label} - ${content}` : label
    default:
      return label
  }
}

// Shorter display for badges and selected values
const getShortDisplayText = (element: TextElement, type: TextElementType): string => {
  const { label, content } = element
  
  switch (type) {
    case 'title':
    case 'footnote':
      // For badges, show truncated content if available
      if (content) {
        const truncated = content.length > 30 ? content.substring(0, 30) + '...' : content
        return `[${label}] ${truncated}`
      }
      // If no content, label IS the text - truncate it
      const truncatedLabel = label.length > 35 ? label.substring(0, 35) + '...' : label
      return truncatedLabel
    case 'population_set':
    case 'acronyms_set':
    case 'ich_category':
      // Show short form/abbreviation/code for badges
      return content ? `${label} - ${content}` : label
    default:
      return label
  }
}

// Get unique categories from text elements (for titles/footnotes)
const getCategories = (elements: TextElement[]): string[] => {
  const categories = [...new Set(elements.map(el => el.label))]
  return categories.sort()
}

interface TextElementComboboxProps {
  type: TextElementType
  value?: number | null // Selected ID for single-select
  values?: number[] // Selected IDs for multi-select
  onChange?: (id: number | null) => void // For single-select
  onMultiChange?: (ids: number[]) => void // For multi-select
  multiple?: boolean
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function TextElementCombobox({
  type,
  value,
  values = [],
  onChange,
  onMultiChange,
  multiple = false,
  placeholder = 'Search or create...',
  disabled = false,
  className
}: TextElementComboboxProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [isCreating, setIsCreating] = useState(false)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newItemLabel, setNewItemLabel] = useState('')
  const [newItemContent, setNewItemContent] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  // Get field config for this type
  const fieldConfig = TYPE_FIELD_CONFIG[type]

  // Check if this type supports category filtering (titles and footnotes)
  const supportsCategoryFilter = type === 'title' || type === 'footnote'

  // Fetch all text elements of this type
  const { data: textElements = [], isLoading } = useQuery({
    queryKey: ['text-elements', type],
    queryFn: () => textElementsApi.getByType(type),
  })

  // Get available categories for filtering
  const categories = useMemo(() => getCategories(textElements), [textElements])

  // Create mutation with both label and content
  const createMutation = useMutation({
    mutationFn: (data: { label: string; content?: string }) => 
      textElementsApi.create({ type, label: data.label, content: data.content }),
    onSuccess: (newElement) => {
      queryClient.invalidateQueries({ queryKey: ['text-elements', type] })
      if (multiple && onMultiChange) {
        onMultiChange([...values, newElement.id])
      } else if (onChange) {
        onChange(newElement.id)
      }
      setSearch('')
      setIsCreating(false)
      setCreateDialogOpen(false)
      setNewItemLabel('')
      setNewItemContent('')
      if (!multiple) setOpen(false)
    },
    onError: () => {
      setIsCreating(false)
    }
  })

  // Filter text elements based on search and category
  const filteredElements = useMemo(() => {
    let filtered = textElements
    
    // Apply category filter for titles/footnotes
    if (supportsCategoryFilter && categoryFilter !== 'all') {
      filtered = filtered.filter(el => el.label === categoryFilter)
    }
    
    // Apply text search (search in both label and content)
    if (search) {
      const searchLower = search.toLowerCase()
      filtered = filtered.filter(el => 
        el.label.toLowerCase().includes(searchLower) ||
        (el.content && el.content.toLowerCase().includes(searchLower))
      )
    }
    
    return filtered
  }, [textElements, search, categoryFilter, supportsCategoryFilter])

  // Check if exact match exists (by label for create functionality)
  const exactMatch = textElements.find(
    el => el.label.toLowerCase() === search.toLowerCase()
  )

  // Get selected element(s) for display
  const selectedElement = value ? textElements.find(el => el.id === value) : null
  const selectedElements = values
    .map(id => textElements.find(el => el.id === id))
    .filter((el): el is TextElement => el !== undefined)

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (element: TextElement) => {
    if (multiple && onMultiChange) {
      if (values.includes(element.id)) {
        onMultiChange(values.filter(id => id !== element.id))
      } else {
        onMultiChange([...values, element.id])
      }
      setSearch('')
    } else if (onChange) {
      onChange(element.id)
      setSearch('')
      setOpen(false)
    }
  }

  // Open create dialog with search text pre-filled
  const handleOpenCreateDialog = () => {
    // Pre-fill based on search text
    if (search.trim()) {
      // For titles/footnotes, assume search is the content
      if (type === 'title' || type === 'footnote') {
        setNewItemLabel('')
        setNewItemContent(search.trim())
      } else {
        // For others, assume search is the label (short form/abbreviation/code)
        setNewItemLabel(search.trim())
        setNewItemContent('')
      }
    } else {
      setNewItemLabel('')
      setNewItemContent('')
    }
    setCreateDialogOpen(true)
  }

  // Actually create the item from dialog
  const handleCreateFromDialog = () => {
    if (!newItemLabel.trim()) return
    
    setIsCreating(true)
    createMutation.mutate({
      label: newItemLabel.trim(),
      content: newItemContent.trim() || undefined
    })
  }

  const handleRemove = (id: number) => {
    if (multiple && onMultiChange) {
      onMultiChange(values.filter(v => v !== id))
    } else if (onChange) {
      onChange(null)
    }
  }

  const handleClear = () => {
    if (onChange) onChange(null)
    setSearch('')
  }

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      {/* Single Select Display */}
      {!multiple && (
        <div className="relative">
          <div
            className={cn(
              'flex h-10 w-full items-center justify-between gap-2 rounded-md border border-input bg-background px-3 py-2 text-sm cursor-pointer',
              disabled && 'cursor-not-allowed opacity-50',
              open && 'ring-2 ring-ring ring-offset-2'
            )}
            onClick={() => !disabled && setOpen(!open)}
          >
            {selectedElement ? (
              <span className="flex-1 min-w-0 truncate" title={getDisplayText(selectedElement, type)}>
                {getShortDisplayText(selectedElement, type)}
              </span>
            ) : (
              <span className="text-muted-foreground flex-1">{placeholder}</span>
            )}
            <div className="flex items-center gap-1 flex-shrink-0">
              {selectedElement && !disabled && (
                <X
                  className="h-4 w-4 text-muted-foreground hover:text-foreground"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleClear()
                  }}
                />
              )}
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </div>
          </div>
        </div>
      )}

      {/* Multi Select Display */}
      {multiple && (
        <div
          className={cn(
            'flex min-h-10 w-full flex-wrap gap-1 rounded-md border border-input bg-background px-3 py-2 cursor-text',
            disabled && 'cursor-not-allowed opacity-50',
            open && 'ring-2 ring-ring ring-offset-2'
          )}
          onClick={() => {
            if (!disabled) {
              setOpen(true)
              inputRef.current?.focus()
            }
          }}
        >
          {selectedElements.map(el => (
            <Badge
              key={el.id}
              variant="secondary"
              className="gap-1 max-w-[200px]"
              title={getDisplayText(el, type)}
            >
              <span className="truncate">{getShortDisplayText(el, type)}</span>
              {!disabled && (
                <X
                  className="h-3 w-3 cursor-pointer hover:text-destructive flex-shrink-0"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleRemove(el.id)
                  }}
                />
              )}
            </Badge>
          ))}
          <input
            ref={inputRef}
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => setOpen(true)}
            placeholder={selectedElements.length === 0 ? placeholder : ''}
            disabled={disabled}
            className="flex-1 min-w-[100px] bg-transparent outline-none text-sm"
          />
        </div>
      )}

      {/* Dropdown */}
      {open && !disabled && (
        <div className="absolute z-50 w-full mt-1 rounded-md border bg-popover text-popover-foreground shadow-md">
          {/* Search input and category filter */}
          <div className="p-2 border-b space-y-2">
            {/* Category filter for titles/footnotes */}
            {supportsCategoryFilter && categories.length > 0 && (
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(cat => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {/* Search input */}
            {!multiple && (
              <Input
                ref={inputRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Type to search..."
                autoFocus
                className="h-8"
              />
            )}
          </div>

          {/* Options list */}
          <div className="max-h-60 overflow-auto p-1">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            ) : filteredElements.length === 0 && !search ? (
              <div className="py-4 text-center text-sm text-muted-foreground">
                No items found. Type to create one.
              </div>
            ) : (
              <>
                {filteredElements.map(element => {
                  const isSelected = multiple 
                    ? values.includes(element.id)
                    : value === element.id

                  return (
                    <div
                      key={element.id}
                      onClick={() => handleSelect(element)}
                      className={cn(
                        'flex items-center gap-2 px-2 py-1.5 text-sm rounded-sm cursor-pointer',
                        isSelected && 'bg-accent',
                        !isSelected && 'hover:bg-accent/50'
                      )}
                      title={getDisplayText(element, type)}
                    >
                      <div className={cn(
                        'flex h-4 w-4 items-center justify-center flex-shrink-0',
                        multiple && 'border rounded-sm',
                        isSelected && multiple && 'bg-primary border-primary'
                      )}>
                        {isSelected && (
                          <Check className={cn(
                            'h-3 w-3',
                            multiple ? 'text-primary-foreground' : 'text-primary'
                          )} />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        {(type === 'title' || type === 'footnote') ? (
                          element.content ? (
                            // Has both category (label) and content
                            <div className="flex flex-col">
                              <span className="text-xs text-muted-foreground font-medium">{element.label}</span>
                              <span className="truncate">{element.content}</span>
                            </div>
                          ) : (
                            // Label IS the content (inline created or legacy data)
                            <span className="truncate">{element.label}</span>
                          )
                        ) : (
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{element.label}</span>
                            {element.content && (
                              <>
                                <span className="text-muted-foreground">-</span>
                                <span className="truncate text-muted-foreground">{element.content}</span>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}

                {/* Create new option - always visible */}
                <div
                  onClick={handleOpenCreateDialog}
                  className={cn(
                    'flex items-center gap-2 px-2 py-1.5 text-sm rounded-sm cursor-pointer',
                    'hover:bg-accent/50 text-primary border-t mt-1 pt-2'
                  )}
                >
                  <Plus className="h-4 w-4" />
                  <span>+ Add new {fieldConfig.labelField.toLowerCase()}...</span>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Create New Item Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Add New {type === 'title' ? 'Title' : type === 'footnote' ? 'Footnote' : type === 'population_set' ? 'Population' : type === 'acronyms_set' ? 'Acronym' : 'ICH Category'}</DialogTitle>
            <DialogDescription>
              Enter both the {fieldConfig.labelField.toLowerCase()} and {fieldConfig.contentField.toLowerCase()}.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="new-item-label">{fieldConfig.labelField} *</Label>
              {/* For titles/footnotes, show category dropdown with existing categories */}
              {(type === 'title' || type === 'footnote') ? (
                <Select
                  value={newItemLabel || '__custom__'}
                  onValueChange={(val) => {
                    if (val === '__custom__') {
                      setNewItemLabel('')
                    } else {
                      setNewItemLabel(val)
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select or create category" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.length > 0 && (
                      <>
                        {categories.map(cat => (
                          <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                        ))}
                        <SelectItem value="__custom__">
                          <span className="text-primary">+ Add new category...</span>
                        </SelectItem>
                      </>
                    )}
                    {categories.length === 0 && (
                      <SelectItem value="__custom__">
                        <span className="text-primary">+ Add new category...</span>
                      </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  id="new-item-label"
                  value={newItemLabel}
                  onChange={(e) => setNewItemLabel(e.target.value)}
                  placeholder={fieldConfig.labelPlaceholder}
                />
              )}
              {/* Show custom input when "Add new category" is selected */}
              {(type === 'title' || type === 'footnote') && (newItemLabel === '' || !categories.includes(newItemLabel)) && (
                <Input
                  value={newItemLabel}
                  onChange={(e) => setNewItemLabel(e.target.value)}
                  placeholder="Enter new category name..."
                  className="mt-2"
                />
              )}
              <p className="text-xs text-muted-foreground">{fieldConfig.labelHelp}</p>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="new-item-content">{fieldConfig.contentField} *</Label>
              {(type === 'title' || type === 'footnote') ? (
                <Textarea
                  id="new-item-content"
                  value={newItemContent}
                  onChange={(e) => setNewItemContent(e.target.value)}
                  placeholder={fieldConfig.contentPlaceholder}
                  rows={3}
                />
              ) : (
                <Input
                  id="new-item-content"
                  value={newItemContent}
                  onChange={(e) => setNewItemContent(e.target.value)}
                  placeholder={fieldConfig.contentPlaceholder}
                />
              )}
              <p className="text-xs text-muted-foreground">{fieldConfig.contentHelp}</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateFromDialog} 
              disabled={!newItemLabel.trim() || !newItemContent.trim() || isCreating}
            >
              {isCreating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}










