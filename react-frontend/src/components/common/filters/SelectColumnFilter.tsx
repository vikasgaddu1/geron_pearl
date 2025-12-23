import { useState, useMemo } from 'react'
import { Check, X, Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import { matchWildcard } from '@/lib/filterUtils'

interface SelectColumnFilterProps {
  options: string[]
  value?: string[]
  onChange: (value: string[]) => void
  placeholder?: string
  className?: string
}

export function SelectColumnFilter({
  options,
  value = [],
  onChange,
  placeholder = 'Search options...',
  className,
}: SelectColumnFilterProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedValues, setSelectedValues] = useState<string[]>(value)

  // Filter options based on search term (supports wildcards)
  const filteredOptions = useMemo(() => {
    if (!searchTerm) return options
    
    return options.filter((option) =>
      matchWildcard(option, searchTerm)
    )
  }, [options, searchTerm])

  const handleToggle = (option: string) => {
    const newValues = selectedValues.includes(option)
      ? selectedValues.filter((v) => v !== option)
      : [...selectedValues, option]
    
    setSelectedValues(newValues)
    onChange(newValues)
  }

  const handleSelectAll = () => {
    const allFilteredValues = filteredOptions
    setSelectedValues(allFilteredValues)
    onChange(allFilteredValues)
  }

  const handleClearAll = () => {
    setSelectedValues([])
    onChange([])
  }

  const isAllSelected = filteredOptions.length > 0 && 
    filteredOptions.every((option) => selectedValues.includes(option))

  return (
    <div className={cn('space-y-3', className)}>
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={placeholder}
          className="pl-8 pr-8"
        />
        {searchTerm && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-0 top-0 h-full px-2 hover:bg-transparent"
            onClick={() => setSearchTerm('')}
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </Button>
        )}
      </div>

      {/* Select/Clear All Buttons */}
      <div className="flex items-center justify-between gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleSelectAll}
          disabled={isAllSelected}
          className="flex-1"
        >
          Select All
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleClearAll}
          disabled={selectedValues.length === 0}
          className="flex-1"
        >
          Clear All
        </Button>
      </div>

      {/* Options List */}
      <ScrollArea className="h-[200px] rounded-md border p-2">
        {filteredOptions.length === 0 ? (
          <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
            No options found
          </div>
        ) : (
          <div className="space-y-2">
            {filteredOptions.map((option) => {
              const isSelected = selectedValues.includes(option)
              return (
                <div
                  key={option}
                  className="flex items-center space-x-2 rounded-md px-2 py-1.5 hover:bg-accent cursor-pointer"
                  onClick={() => handleToggle(option)}
                >
                  <Checkbox
                    id={`option-${option}`}
                    checked={isSelected}
                    onCheckedChange={() => handleToggle(option)}
                  />
                  <Label
                    htmlFor={`option-${option}`}
                    className="flex-1 cursor-pointer font-normal text-sm"
                  >
                    {option || '(Empty)'}
                  </Label>
                  {isSelected && <Check className="h-4 w-4 text-primary" />}
                </div>
              )
            })}
          </div>
        )}
      </ScrollArea>

      {/* Selection Summary */}
      {selectedValues.length > 0 && (
        <div className="text-xs text-muted-foreground">
          {selectedValues.length} of {options.length} selected
        </div>
      )}

      {/* Tips */}
      <div className="text-xs text-muted-foreground">
        <p className="font-medium">Tips:</p>
        <ul className="list-disc list-inside space-y-0.5 ml-1">
          <li>Type to filter options</li>
          <li>Use * for wildcards: *admin</li>
          <li>Multiple selections = OR logic</li>
        </ul>
      </div>
    </div>
  )
}


