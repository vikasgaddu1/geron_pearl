import { ReactNode, useState, useMemo, useRef, useEffect } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  SortingState,
  ColumnFiltersState,
  ColumnDef as TanStackColumnDef,
} from '@tanstack/react-table'
import { ArrowUpDown, ArrowUp, ArrowDown, X, ChevronRight } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { HelpIcon } from './HelpIcon'
import { ColumnFilterPopover } from './filters/ColumnFilterPopover'
import { TextColumnFilter } from './filters/TextColumnFilter'
import { SelectColumnFilter } from './filters/SelectColumnFilter'
import { DateRangeFilter, DateRange } from './filters/DateRangeFilter'
import { cn } from '@/lib/utils'
import { matchText, matchDateRange, matchMultiSelect, getUniqueValues } from '@/lib/filterUtils'

export type FilterType = 'text' | 'select' | 'date' | 'none'

export interface ColumnDef<T> {
  id: string
  header: string
  accessorKey: keyof T
  filterType?: FilterType
  filterOptions?: string[]
  helpText?: string
  cell?: (value: any, row: T) => ReactNode
  enableSorting?: boolean
}

interface DataTableProps<T> {
  data: T[]
  columns: ColumnDef<T>[]
  enablePagination?: boolean
  pageSize?: number
  className?: string
}

export function DataTable<T>({
  data,
  columns,
  enablePagination = false,
  pageSize = 10,
  className,
}: DataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [textFilters, setTextFilters] = useState<Record<string, string>>({})
  const [selectFilters, setSelectFilters] = useState<Record<string, string[]>>({})
  const [dateFilters, setDateFilters] = useState<Record<string, DateRange>>({})
  const [hasHorizontalOverflow, setHasHorizontalOverflow] = useState(false)
  const [isScrolledRight, setIsScrolledRight] = useState(false)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Check for horizontal overflow
  useEffect(() => {
    const checkOverflow = () => {
      const container = scrollContainerRef.current
      if (container) {
        const hasOverflow = container.scrollWidth > container.clientWidth
        setHasHorizontalOverflow(hasOverflow)
        setIsScrolledRight(container.scrollLeft > 0)
      }
    }

    checkOverflow()
    window.addEventListener('resize', checkOverflow)
    
    const container = scrollContainerRef.current
    if (container) {
      container.addEventListener('scroll', () => {
        setIsScrolledRight(container.scrollLeft > 0)
        // Check if scrolled to end
        const atEnd = container.scrollLeft + container.clientWidth >= container.scrollWidth - 5
        setHasHorizontalOverflow(!atEnd)
      })
    }

    return () => window.removeEventListener('resize', checkOverflow)
  }, [data, columns])

  // Build TanStack Table columns
  const tableColumns: TanStackColumnDef<T>[] = useMemo(() => {
    return columns.map((col) => ({
      id: col.id,
      accessorKey: col.accessorKey as string,
      header: ({ column }) => {
        const isSorted = column.getIsSorted()
        const canSort = col.enableSorting !== false
        const filterType = col.filterType || 'none'
        const hasFilter = filterType !== 'none'
        const columnId = col.id
        
        // Check if filter is active
        const isFilterActive = 
          (textFilters[columnId] && textFilters[columnId].length > 0) ||
          (selectFilters[columnId] && selectFilters[columnId].length > 0) ||
          (dateFilters[columnId] && (dateFilters[columnId].from || dateFilters[columnId].to))

        const handleTextFilterChange = (value: string) => {
          setTextFilters((prev) => ({ ...prev, [columnId]: value }))
        }

        const handleSelectFilterChange = (values: string[]) => {
          setSelectFilters((prev) => ({ ...prev, [columnId]: values }))
        }

        const handleDateFilterChange = (range: DateRange) => {
          setDateFilters((prev) => ({ ...prev, [columnId]: range }))
        }

        const handleClearFilter = () => {
          setTextFilters((prev) => ({ ...prev, [columnId]: '' }))
          setSelectFilters((prev) => ({ ...prev, [columnId]: [] }))
          setDateFilters((prev) => ({ ...prev, [columnId]: { from: undefined, to: undefined } }))
        }

        const getFilterSummary = () => {
          if (textFilters[columnId]) return `"${textFilters[columnId]}"`
          if (selectFilters[columnId]?.length > 0) return `${selectFilters[columnId].length} selected`
          if (dateFilters[columnId]?.from || dateFilters[columnId]?.to) {
            const from = dateFilters[columnId].from ? dateFilters[columnId].from!.toLocaleDateString() : '...'
            const to = dateFilters[columnId].to ? dateFilters[columnId].to!.toLocaleDateString() : '...'
            return `${from} to ${to}`
          }
          return ''
        }

        return (
          <div className="flex flex-col gap-0.5">
            {/* Column name */}
            <span className="font-medium text-xs">{col.header}</span>
            
            {/* Icons row - sort, filter, help */}
            {(canSort || hasFilter || col.helpText) && (
              <div className="flex items-center gap-0.5">
                {canSort && (
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                    className="h-5 w-5 p-0"
                  >
                    {isSorted === 'asc' && <ArrowUp className="h-3 w-3" />}
                    {isSorted === 'desc' && <ArrowDown className="h-3 w-3" />}
                    {!isSorted && <ArrowUpDown className="h-3 w-3 opacity-50" />}
                  </Button>
                )}
                
                {hasFilter && (
                  <ColumnFilterPopover
                    isActive={isFilterActive}
                    onClear={handleClearFilter}
                    filterSummary={getFilterSummary()}
                  >
                    {filterType === 'text' && (
                      <TextColumnFilter
                        value={textFilters[columnId] || ''}
                        onChange={handleTextFilterChange}
                        placeholder={`Filter ${col.header.toLowerCase()}...`}
                      />
                    )}
                    {filterType === 'select' && (
                      <SelectColumnFilter
                        options={col.filterOptions || getUniqueValues(data, col.accessorKey)}
                        value={selectFilters[columnId] || []}
                        onChange={handleSelectFilterChange}
                        placeholder={`Search ${col.header.toLowerCase()}...`}
                      />
                    )}
                    {filterType === 'date' && (
                      <DateRangeFilter
                        value={dateFilters[columnId]}
                        onChange={handleDateFilterChange}
                      />
                    )}
                  </ColumnFilterPopover>
                )}
                
                {col.helpText && (
                  <HelpIcon
                    title={col.header}
                    content={col.helpText}
                  />
                )}
              </div>
            )}
          </div>
        )
      },
      cell: ({ row, getValue }) => {
        const value = getValue()
        if (col.cell) {
          return col.cell(value, row.original)
        }
        return value as ReactNode
      },
      filterFn: (row, columnId, filterValue) => {
        const value = row.getValue(columnId) as string
        const col = columns.find((c) => c.id === columnId)
        
        if (!col) return true
        
        if (col.filterType === 'text') {
          const textFilter = textFilters[columnId]
          if (!textFilter) return true
          return matchText(value, textFilter, 'wildcard')
        }
        
        if (col.filterType === 'select') {
          const selectFilter = selectFilters[columnId]
          if (!selectFilter || selectFilter.length === 0) return true
          return matchMultiSelect(value, selectFilter)
        }
        
        if (col.filterType === 'date') {
          const dateFilter = dateFilters[columnId]
          if (!dateFilter || (!dateFilter.from && !dateFilter.to)) return true
          return matchDateRange(value, dateFilter.from, dateFilter.to)
        }
        
        return true
      },
    }))
  }, [columns, data, textFilters, selectFilters, dateFilters])

  const table = useReactTable({
    data,
    columns: tableColumns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: enablePagination ? getPaginationRowModel() : undefined,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    state: {
      sorting,
      columnFilters,
    },
    initialState: {
      pagination: enablePagination ? { pageSize } : undefined,
    },
  })

  // Get active filters for summary
  const activeFilters = useMemo(() => {
    const filters: Array<{ id: string; label: string; summary: string }> = []
    
    Object.entries(textFilters).forEach(([id, value]) => {
      if (value) {
        const col = columns.find((c) => c.id === id)
        filters.push({
          id,
          label: col?.header || id,
          summary: `"${value}"`,
        })
      }
    })
    
    Object.entries(selectFilters).forEach(([id, values]) => {
      if (values && values.length > 0) {
        const col = columns.find((c) => c.id === id)
        filters.push({
          id,
          label: col?.header || id,
          summary: values.length === 1 ? values[0] : `${values.length} selected`,
        })
      }
    })
    
    Object.entries(dateFilters).forEach(([id, range]) => {
      if (range && (range.from || range.to)) {
        const col = columns.find((c) => c.id === id)
        const from = range.from ? range.from.toLocaleDateString() : '...'
        const to = range.to ? range.to.toLocaleDateString() : '...'
        filters.push({
          id,
          label: col?.header || id,
          summary: `${from} to ${to}`,
        })
      }
    })
    
    return filters
  }, [textFilters, selectFilters, dateFilters, columns])

  const clearAllFilters = () => {
    setTextFilters({})
    setSelectFilters({})
    setDateFilters({})
  }

  const clearFilter = (filterId: string) => {
    setTextFilters((prev) => ({ ...prev, [filterId]: '' }))
    setSelectFilters((prev) => ({ ...prev, [filterId]: [] }))
    setDateFilters((prev) => ({ ...prev, [filterId]: { from: undefined, to: undefined } }))
  }

  return (
    <div className={cn('space-y-4 w-full', className)}>
      {/* Active Filters Summary */}
      {activeFilters.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Active filters:</span>
          {activeFilters.map((filter) => (
            <Badge key={filter.id} variant="secondary" className="gap-1">
              <span className="font-medium">{filter.label}:</span>
              <span>{filter.summary}</span>
              <Button
                variant="ghost"
                size="icon"
                className="h-3 w-3 p-0 hover:bg-transparent ml-1"
                onClick={() => clearFilter(filter.id)}
              >
                <X className="h-2.5 w-2.5" />
              </Button>
            </Badge>
          ))}
          <Button
            variant="ghost"
            size="sm"
            onClick={clearAllFilters}
            className="h-6 text-xs"
          >
            Clear All
          </Button>
        </div>
      )}

      {/* Table with horizontal scroll indicator */}
      <div className="relative w-full">
        {/* Scroll indicator - right side */}
        {hasHorizontalOverflow && (
          <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-background via-background/80 to-transparent pointer-events-none z-10 flex items-center justify-end pr-1">
            <ChevronRight className="h-5 w-5 text-muted-foreground animate-pulse" />
          </div>
        )}
        {/* Scroll indicator - left side (when scrolled) */}
        {isScrolledRight && (
          <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-background via-background/80 to-transparent pointer-events-none z-10" />
        )}
        
        <div 
          ref={scrollContainerRef}
          className="rounded-md border overflow-x-auto scrollbar-thin scrollbar-thumb-muted-foreground/30 scrollbar-track-transparent"
        >
          <Table className="w-full min-w-max">
            <TableHeader className="sticky top-0 bg-background z-20">
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id} className="bg-muted/50">
                  {headerGroup.headers.map((header) => (
                    <TableHead key={header.id} className="whitespace-nowrap">
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows?.length ? (
                table.getRowModel().rows.map((row) => (
                  <TableRow
                    key={row.id}
                    data-state={row.getIsSelected() && 'selected'}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id} className="whitespace-nowrap">
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell
                    colSpan={columns.length}
                    className="h-24 text-center"
                  >
                    No results found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Pagination */}
      {enablePagination && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Showing {table.getState().pagination.pageIndex * pageSize + 1} to{' '}
            {Math.min(
              (table.getState().pagination.pageIndex + 1) * pageSize,
              table.getFilteredRowModel().rows.length
            )}{' '}
            of {table.getFilteredRowModel().rows.length} results
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}


