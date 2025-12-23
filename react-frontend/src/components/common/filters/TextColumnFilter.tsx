import { useState, useEffect } from 'react'
import { X, Sparkles } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'
import { hasWildcard, looksLikeRegex } from '@/lib/filterUtils'

interface TextColumnFilterProps {
  value?: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function TextColumnFilter({
  value = '',
  onChange,
  placeholder = 'Search...',
  className,
}: TextColumnFilterProps) {
  const [filterValue, setFilterValue] = useState(value)
  const [regexMode, setRegexMode] = useState(false)
  const [isRegexValid, setIsRegexValid] = useState(true)

  // Sync with external value changes
  useEffect(() => {
    setFilterValue(value)
  }, [value])

  // Auto-detect regex mode
  useEffect(() => {
    if (filterValue && !hasWildcard(filterValue) && looksLikeRegex(filterValue)) {
      setRegexMode(true)
    }
  }, [filterValue])

  // Validate regex when in regex mode
  useEffect(() => {
    if (regexMode && filterValue) {
      try {
        new RegExp(filterValue)
        setIsRegexValid(true)
      } catch {
        setIsRegexValid(false)
      }
    } else {
      setIsRegexValid(true)
    }
  }, [regexMode, filterValue])

  const handleChange = (newValue: string) => {
    setFilterValue(newValue)
    onChange(newValue)
  }

  const handleClear = () => {
    setFilterValue('')
    onChange('')
    setRegexMode(false)
  }

  const getFilterMode = () => {
    if (regexMode) return 'Regex'
    if (hasWildcard(filterValue)) return 'Wildcard'
    return 'Text'
  }

  const filterMode = getFilterMode()

  return (
    <div className={cn('space-y-3', className)}>
      <div className="space-y-2">
        <div className="relative">
          <Input
            value={filterValue}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={placeholder}
            className={cn(
              'pr-8',
              !isRegexValid && 'border-destructive focus-visible:ring-destructive'
            )}
          />
          {filterValue && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-0 top-0 h-full px-2 hover:bg-transparent"
              onClick={handleClear}
            >
              <X className="h-4 w-4 text-muted-foreground" />
            </Button>
          )}
        </div>
        {!isRegexValid && (
          <p className="text-xs text-destructive">Invalid regex pattern</p>
        )}
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Switch
            id="regex-mode"
            checked={regexMode}
            onCheckedChange={setRegexMode}
          />
          <Label
            htmlFor="regex-mode"
            className="text-xs font-normal cursor-pointer"
          >
            Regex mode
          </Label>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Sparkles className="h-3 w-3" />
          <span>{filterMode}</span>
        </div>
      </div>

      <div className="text-xs text-muted-foreground space-y-1">
        <p className="font-medium">Tips:</p>
        <ul className="list-disc list-inside space-y-0.5 ml-1">
          <li>Use * for wildcards: test* or *001</li>
          <li>Enable regex for patterns: ^ABC-\d+$</li>
          <li>Case-insensitive by default</li>
        </ul>
      </div>
    </div>
  )
}


