import { useState, useCallback } from 'react'
import { Upload, Download, FileSpreadsheet, X, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'

export interface ColumnDefinition {
  key: string
  label: string
  required?: boolean
  validate?: (value: string) => boolean | string
}

export interface ExcelUploadProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  columns: ColumnDefinition[]
  sampleData?: string[][]
  onUpload: (data: Record<string, string>[]) => Promise<void>
  templateFilename?: string
}

export function ExcelUpload({
  open,
  onOpenChange,
  title,
  description,
  columns,
  sampleData = [],
  onUpload,
  templateFilename = 'template.csv',
}: ExcelUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<Record<string, string>[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [isUploading, setIsUploading] = useState(false)

  const downloadTemplate = useCallback(() => {
    const headers = columns.map((c) => c.key)
    const rows = sampleData.length > 0 ? sampleData : [headers.map(() => '')]
    const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n')
    
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = templateFilename
    a.click()
    URL.revokeObjectURL(url)
  }, [columns, sampleData, templateFilename])

  const parseFile = useCallback((file: File) => {
    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target?.result as string
      const lines = text.split('\n').filter((line) => line.trim())
      
      if (lines.length === 0) {
        setErrors(['File is empty'])
        return
      }

      // Parse headers
      const headers = lines[0].split(',').map((h) => h.trim().toLowerCase().replace(/\s+/g, '_'))
      
      // Map headers to column keys
      const headerMap = new Map<number, string>()
      columns.forEach((col) => {
        const index = headers.findIndex(
          (h) => h === col.key.toLowerCase() || h === col.label.toLowerCase().replace(/\s+/g, '_')
        )
        if (index !== -1) {
          headerMap.set(index, col.key)
        }
      })

      // Check for missing required columns
      const missingRequired = columns
        .filter((c) => c.required)
        .filter((c) => !Array.from(headerMap.values()).includes(c.key))
        .map((c) => c.label)

      if (missingRequired.length > 0) {
        setErrors([`Missing required columns: ${missingRequired.join(', ')}`])
        return
      }

      // Parse data rows
      const data: Record<string, string>[] = []
      const rowErrors: string[] = []

      for (let i = 1; i < lines.length; i++) {
        const values = parseCSVLine(lines[i])
        const row: Record<string, string> = {}
        
        headerMap.forEach((colKey, index) => {
          row[colKey] = values[index]?.trim() || ''
        })

        // Validate row
        columns.forEach((col) => {
          const value = row[col.key] || ''
          if (col.required && !value) {
            rowErrors.push(`Row ${i}: ${col.label} is required`)
          } else if (col.validate && value) {
            const result = col.validate(value)
            if (result !== true && typeof result === 'string') {
              rowErrors.push(`Row ${i}: ${result}`)
            } else if (result === false) {
              rowErrors.push(`Row ${i}: Invalid ${col.label}`)
            }
          }
        })

        data.push(row)
      }

      setPreview(data)
      setErrors(rowErrors.slice(0, 5)) // Show first 5 errors
      if (rowErrors.length > 5) {
        setErrors((prev) => [...prev, `...and ${rowErrors.length - 5} more errors`])
      }
    }
    reader.readAsText(file)
  }, [columns])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return
    
    setFile(selectedFile)
    setErrors([])
    parseFile(selectedFile)
  }

  const handleUpload = async () => {
    if (preview.length === 0) return
    
    setIsUploading(true)
    try {
      await onUpload(preview)
      handleClose()
    } catch (error) {
      setErrors([error instanceof Error ? error.message : 'Upload failed'])
    } finally {
      setIsUploading(false)
    }
  }

  const handleClose = () => {
    setFile(null)
    setPreview([])
    setErrors([])
    onOpenChange(false)
  }

  const validRowCount = preview.filter((row) => 
    columns.filter((c) => c.required).every((c) => row[c.key])
  ).length

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-3xl max-h-[85vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            {title}
          </DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>

        <div className="space-y-4">
          {/* Template Download & File Upload */}
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={downloadTemplate}>
              <Download className="h-4 w-4 mr-2" />
              Download Template
            </Button>
            <div className="flex-1">
              <Label htmlFor="file-upload" className="sr-only">
                Choose file
              </Label>
              <Input
                id="file-upload"
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileChange}
                className="cursor-pointer"
              />
            </div>
          </div>

          {/* Column Info */}
          <div className="flex flex-wrap gap-2">
            {columns.map((col) => (
              <Badge key={col.key} variant={col.required ? 'default' : 'secondary'}>
                {col.label}
                {col.required && ' *'}
              </Badge>
            ))}
          </div>

          {/* Errors */}
          {errors.length > 0 && (
            <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                <div className="space-y-1">
                  {errors.map((error, index) => (
                    <p key={index} className="text-sm text-destructive">
                      {error}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Preview */}
          {preview.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Preview ({validRowCount} valid rows)</Label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setFile(null)
                    setPreview([])
                    setErrors([])
                  }}
                >
                  <X className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              </div>
              <ScrollArea className="h-64 rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {columns.map((col) => (
                        <TableHead key={col.key}>{col.label}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {preview.slice(0, 20).map((row, index) => {
                      const isValid = columns
                        .filter((c) => c.required)
                        .every((c) => row[c.key])
                      return (
                        <TableRow
                          key={index}
                          className={!isValid ? 'bg-destructive/5' : ''}
                        >
                          {columns.map((col) => (
                            <TableCell
                              key={col.key}
                              className={
                                col.required && !row[col.key]
                                  ? 'text-destructive'
                                  : ''
                              }
                            >
                              {row[col.key] || '-'}
                            </TableCell>
                          ))}
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </ScrollArea>
              {preview.length > 20 && (
                <p className="text-center text-sm text-muted-foreground">
                  ...and {preview.length - 20} more rows
                </p>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={validRowCount === 0 || isUploading}
          >
            <Upload className="h-4 w-4 mr-2" />
            {isUploading ? 'Uploading...' : `Upload ${validRowCount} Items`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Helper to parse CSV lines (handles quoted values)
function parseCSVLine(line: string): string[] {
  const result: string[] = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  result.push(current.trim())

  return result
}

