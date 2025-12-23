import React, { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, X, Plus, Loader2, ChevronDown } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { textElementsApi } from '@/api'
import type { TextElement, TextElementType } from '@/types'

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
  const [isCreating, setIsCreating] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  // Fetch all text elements of this type
  const { data: textElements = [], isLoading, error: fetchError } = useQuery({
    queryKey: ['text-elements', type],
    queryFn: () => textElementsApi.getByType(type),
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (label: string) => textElementsApi.create({ type, label }),
    onSuccess: (newElement) => {
      queryClient.invalidateQueries({ queryKey: ['text-elements', type] })
      if (multiple && onMultiChange) {
        onMultiChange([...values, newElement.id])
      } else if (onChange) {
        onChange(newElement.id)
      }
      setSearch('')
      setIsCreating(false)
      if (!multiple) setOpen(false)
    },
    onError: () => {
      setIsCreating(false)
    }
  })

  // Filter text elements based on search
  const filteredElements = textElements.filter(el => 
    el.label.toLowerCase().includes(search.toLowerCase())
  )

  // Check if exact match exists
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

  const handleCreate = () => {
    if (search.trim() && !exactMatch && !isCreating) {
      setIsCreating(true)
      createMutation.mutate(search.trim())
    }
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
              'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm cursor-pointer',
              disabled && 'cursor-not-allowed opacity-50',
              open && 'ring-2 ring-ring ring-offset-2'
            )}
            onClick={() => !disabled && setOpen(!open)}
          >
            {selectedElement ? (
              <span className="truncate">{selectedElement.label}</span>
            ) : (
              <span className="text-muted-foreground">{placeholder}</span>
            )}
            <div className="flex items-center gap-1">
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
              className="gap-1"
            >
              {el.label}
              {!disabled && (
                <X
                  className="h-3 w-3 cursor-pointer hover:text-destructive"
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
          {/* Search input for single select */}
          {!multiple && (
            <div className="p-2 border-b">
              <Input
                ref={inputRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Type to search..."
                autoFocus
                className="h-8"
              />
            </div>
          )}

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
                    >
                      <div className={cn(
                        'flex h-4 w-4 items-center justify-center',
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
                      <span className="truncate">{element.label}</span>
                    </div>
                  )
                })}

                {/* Create new option */}
                {search && !exactMatch && (
                  <div
                    onClick={handleCreate}
                    className={cn(
                      'flex items-center gap-2 px-2 py-1.5 text-sm rounded-sm cursor-pointer',
                      'hover:bg-accent/50 text-primary border-t mt-1 pt-2'
                    )}
                  >
                    {isCreating ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )}
                    <span>Create "{search}"</span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

