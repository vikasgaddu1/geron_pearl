import { useState, useEffect } from 'react'
import { Calendar as CalendarIcon, X } from 'lucide-react'
import { format, subDays, startOfMonth, endOfMonth, startOfDay, endOfDay } from 'date-fns'
import { Calendar } from '@/components/ui/calendar'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'

export interface DateRange {
  from: Date | undefined
  to: Date | undefined
}

interface DateRangeFilterProps {
  value?: DateRange
  onChange: (range: DateRange) => void
  className?: string
}

const PRESETS = [
  { label: 'Today', getValue: () => ({ from: startOfDay(new Date()), to: endOfDay(new Date()) }) },
  { label: 'Last 7 days', getValue: () => ({ from: subDays(new Date(), 7), to: new Date() }) },
  { label: 'Last 30 days', getValue: () => ({ from: subDays(new Date(), 30), to: new Date() }) },
  { label: 'This month', getValue: () => ({ from: startOfMonth(new Date()), to: endOfMonth(new Date()) }) },
]

export function DateRangeFilter({
  value,
  onChange,
  className,
}: DateRangeFilterProps) {
  const [dateRange, setDateRange] = useState<DateRange>({
    from: value?.from,
    to: value?.to,
  })
  const [fromCalendarOpen, setFromCalendarOpen] = useState(false)
  const [toCalendarOpen, setToCalendarOpen] = useState(false)

  useEffect(() => {
    setDateRange({
      from: value?.from,
      to: value?.to,
    })
  }, [value])

  const handleFromDateChange = (date: Date | undefined) => {
    const newRange = { ...dateRange, from: date }
    setDateRange(newRange)
    onChange(newRange)
    setFromCalendarOpen(false)
  }

  const handleToDateChange = (date: Date | undefined) => {
    const newRange = { ...dateRange, to: date }
    setDateRange(newRange)
    onChange(newRange)
    setToCalendarOpen(false)
  }

  const handlePreset = (preset: typeof PRESETS[0]) => {
    const range = preset.getValue()
    setDateRange(range)
    onChange(range)
  }

  const handleClear = () => {
    const emptyRange = { from: undefined, to: undefined }
    setDateRange(emptyRange)
    onChange(emptyRange)
  }

  const hasDateRange = dateRange.from || dateRange.to

  // Validation: ensure from date is before to date
  const isValidRange = !dateRange.from || !dateRange.to || dateRange.from <= dateRange.to

  return (
    <div className={cn('space-y-3', className)}>
      {/* Preset Buttons */}
      <div className="space-y-2">
        <p className="text-xs font-medium">Quick Select:</p>
        <div className="grid grid-cols-2 gap-2">
          {PRESETS.map((preset) => (
            <Button
              key={preset.label}
              variant="outline"
              size="sm"
              onClick={() => handlePreset(preset)}
              className="text-xs"
            >
              {preset.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Custom Date Range */}
      <div className="space-y-2">
        <p className="text-xs font-medium">Custom Range:</p>
        
        {/* From Date */}
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">From:</label>
          <Popover open={fromCalendarOpen} onOpenChange={setFromCalendarOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  'w-full justify-start text-left font-normal',
                  !dateRange.from && 'text-muted-foreground'
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {dateRange.from ? format(dateRange.from, 'PPP') : 'Pick a date'}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={dateRange.from}
                onSelect={handleFromDateChange}
                disabled={(date) =>
                  dateRange.to ? date > dateRange.to : false
                }
                initialFocus
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* To Date */}
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">To:</label>
          <Popover open={toCalendarOpen} onOpenChange={setToCalendarOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  'w-full justify-start text-left font-normal',
                  !dateRange.to && 'text-muted-foreground'
                )}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {dateRange.to ? format(dateRange.to, 'PPP') : 'Pick a date'}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={dateRange.to}
                onSelect={handleToDateChange}
                disabled={(date) =>
                  dateRange.from ? date < dateRange.from : false
                }
                initialFocus
              />
            </PopoverContent>
          </Popover>
        </div>
      </div>

      {/* Validation Message */}
      {!isValidRange && (
        <p className="text-xs text-destructive">
          "From" date must be before "To" date
        </p>
      )}

      {/* Clear Button */}
      {hasDateRange && (
        <Button
          variant="outline"
          size="sm"
          onClick={handleClear}
          className="w-full"
        >
          <X className="mr-2 h-4 w-4" />
          Clear Range
        </Button>
      )}

      {/* Tips */}
      <div className="text-xs text-muted-foreground">
        <p className="font-medium">Tips:</p>
        <ul className="list-disc list-inside space-y-0.5 ml-1">
          <li>Use presets for common ranges</li>
          <li>Select custom dates for precision</li>
          <li>Leave "To" empty for open-ended</li>
        </ul>
      </div>
    </div>
  )
}


