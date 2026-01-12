import { useState, useCallback } from 'react'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { AlertTriangle, RefreshCw, Eye, Trash2, BarChart3 } from 'lucide-react'
import { errorLogsApi, type ErrorLog, type ErrorLogSummary } from '@/api/endpoints/error-logs'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { DataTable, ColumnDef } from '@/components/common/DataTable'
import { TooltipWrapper } from '@/components/common/TooltipWrapper'
import { HelpIcon } from '@/components/common/HelpIcon'
import { formatDateTime } from '@/lib/utils'
import { toast } from 'sonner'

export function ErrorLogsPage() {
  const queryClient = useQueryClient()
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false)
  const [cleanupDialogOpen, setCleanupDialogOpen] = useState(false)
  const [selectedLog, setSelectedLog] = useState<ErrorLog | null>(null)
  const [showSummary, setShowSummary] = useState(true)

  // Query for error logs
  const { data: errorLogs = [], isLoading } = useQuery({
    queryKey: ['errorLogs'],
    queryFn: () => errorLogsApi.getAll({ limit: 500 }),
  })

  // Query for summary statistics
  const { data: summary } = useQuery({
    queryKey: ['errorLogsSummary'],
    queryFn: () => errorLogsApi.getSummary(7),
  })

  // Cleanup mutation
  const cleanupMutation = useMutation({
    mutationFn: (daysToKeep: number) => errorLogsApi.cleanup(daysToKeep),
    onSuccess: (result) => {
      toast.success(`Cleanup complete: ${result.logs_deleted} logs deleted`)
      queryClient.invalidateQueries({ queryKey: ['errorLogs'] })
      queryClient.invalidateQueries({ queryKey: ['errorLogsSummary'] })
      setCleanupDialogOpen(false)
    },
    onError: () => {
      toast.error('Failed to cleanup error logs')
    },
  })

  // Refresh function
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['errorLogs'] })
    queryClient.invalidateQueries({ queryKey: ['errorLogsSummary'] })
  }, [queryClient])

  // View details handler
  const handleViewDetails = (log: ErrorLog) => {
    setSelectedLog(log)
    setDetailsDialogOpen(true)
  }

  // Get severity badge style
  const getSeverityBadge = (severity: string) => {
    const styles: Record<string, string> = {
      INFO: 'bg-blue-100 text-blue-800 border-blue-200',
      WARNING: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      ERROR: 'bg-red-100 text-red-800 border-red-200',
      CRITICAL: 'bg-purple-100 text-purple-800 border-purple-200',
    }
    return styles[severity] || 'bg-gray-100 text-gray-800 border-gray-200'
  }

  // Get source badge style
  const getSourceBadge = (source: string) => {
    const styles: Record<string, string> = {
      BACKEND: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      FRONTEND: 'bg-teal-100 text-teal-800 border-teal-200',
    }
    return styles[source] || 'bg-gray-100 text-gray-800 border-gray-200'
  }

  // Get unique error types for filter options
  const errorTypes = [...new Set(errorLogs.map(log => log.error_type))].sort()

  // Define table columns
  const columns: ColumnDef<ErrorLog>[] = [
    {
      id: 'created_at',
      header: 'Date & Time',
      accessorKey: 'created_at',
      filterType: 'date',
      helpText: 'When the error occurred.',
      cell: (value) => (
        <span className="text-sm whitespace-nowrap">{formatDateTime(value)}</span>
      ),
    },
    {
      id: 'source',
      header: 'Source',
      accessorKey: 'source',
      filterType: 'select',
      filterOptions: ['BACKEND', 'FRONTEND'],
      helpText: 'Whether the error originated from backend or frontend.',
      cell: (value) => (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSourceBadge(value)}`}>
          {value}
        </span>
      ),
    },
    {
      id: 'severity',
      header: 'Severity',
      accessorKey: 'severity',
      filterType: 'select',
      filterOptions: ['INFO', 'WARNING', 'ERROR', 'CRITICAL'],
      helpText: 'Severity level: INFO, WARNING, ERROR, or CRITICAL.',
      cell: (value) => (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSeverityBadge(value)}`}>
          {value}
        </span>
      ),
    },
    {
      id: 'error_type',
      header: 'Error Type',
      accessorKey: 'error_type',
      filterType: 'select',
      filterOptions: errorTypes,
      helpText: 'The type or class of the error.',
      cell: (value) => (
        <span className="font-medium text-sm">{value}</span>
      ),
    },
    {
      id: 'message',
      header: 'Message',
      accessorKey: 'message',
      filterType: 'text',
      helpText: 'Brief description of the error.',
      cell: (value) => (
        <span className="text-sm truncate max-w-[300px] block" title={value}>
          {value.length > 80 ? `${value.substring(0, 80)}...` : value}
        </span>
      ),
    },
    {
      id: 'request_path',
      header: 'Path',
      accessorKey: 'request_path',
      filterType: 'text',
      helpText: 'The URL path where the error occurred.',
      cell: (value) => (
        <span className="font-mono text-xs">{value || '-'}</span>
      ),
    },
    {
      id: 'user_name',
      header: 'User',
      accessorKey: 'user_name',
      filterType: 'text',
      helpText: 'The user who encountered the error (if authenticated).',
      cell: (value, row) => (
        <div>
          <div className="font-medium text-sm">{value || 'Anonymous'}</div>
          {row.user_email && (
            <div className="text-xs text-muted-foreground">{row.user_email}</div>
          )}
        </div>
      ),
    },
    {
      id: 'actions',
      header: 'Details',
      accessorKey: 'id',
      filterType: 'none',
      enableSorting: false,
      cell: (_, log) => (
        <div className="flex justify-center">
          <TooltipWrapper content="View error details">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleViewDetails(log)}
            >
              <Eye className="h-4 w-4" />
            </Button>
          </TooltipWrapper>
        </div>
      ),
    },
  ]

  // Render summary statistics
  const renderSummary = (summary: ErrorLogSummary) => (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardContent className="p-4">
          <div className="text-2xl font-bold">{summary.total_errors}</div>
          <div className="text-sm text-muted-foreground">Total Errors (7 days)</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="text-2xl font-bold text-red-600">
            {(summary.by_severity['ERROR'] || 0) + (summary.by_severity['CRITICAL'] || 0)}
          </div>
          <div className="text-sm text-muted-foreground">Errors + Critical</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="text-2xl font-bold text-indigo-600">
            {summary.by_source['BACKEND'] || 0}
          </div>
          <div className="text-sm text-muted-foreground">Backend Errors</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="text-2xl font-bold text-teal-600">
            {summary.by_source['FRONTEND'] || 0}
          </div>
          <div className="text-sm text-muted-foreground">Frontend Errors</div>
        </CardContent>
      </Card>
    </div>
  )

  if (isLoading) {
    return <PageLoader text="Loading error logs..." />
  }

  return (
    <div className="space-y-6">
      {/* Summary Section */}
      {showSummary && summary && renderSummary(summary)}

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div className="flex items-center gap-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-destructive" />
                Error Logs
              </CardTitle>
              <CardDescription>
                View and analyze application errors from frontend and backend
              </CardDescription>
            </div>
            <HelpIcon
              title="Error Logs"
              content={
                <div className="space-y-2">
                  <p>Monitor errors occurring in both frontend and backend systems.</p>
                  <div className="space-y-1">
                    <p className="font-semibold text-sm">Severity Levels:</p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li><strong>INFO:</strong> Informational messages</li>
                      <li><strong>WARNING:</strong> Potential issues</li>
                      <li><strong>ERROR:</strong> Errors that need attention</li>
                      <li><strong>CRITICAL:</strong> Severe errors requiring immediate action</li>
                    </ul>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Click the eye icon to view full error details including stack traces.
                  </p>
                </div>
              }
            />
          </div>
          <div className="flex gap-2">
            <TooltipWrapper content="Toggle summary statistics">
              <Button
                variant={showSummary ? "default" : "outline"}
                size="sm"
                onClick={() => setShowSummary(!showSummary)}
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                Summary
              </Button>
            </TooltipWrapper>
            <TooltipWrapper content="Cleanup old error logs">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCleanupDialogOpen(true)}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Cleanup
              </Button>
            </TooltipWrapper>
            <TooltipWrapper content="Refresh error logs">
              <Button variant="outline" size="sm" onClick={refetch}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </TooltipWrapper>
          </div>
        </CardHeader>
        <CardContent>
          {errorLogs.length === 0 ? (
            <EmptyState
              icon={AlertTriangle}
              title="No error logs found"
              description="Application errors will appear here as they occur."
            />
          ) : (
            <DataTable
              data={errorLogs}
              columns={columns}
              defaultPageSize={25}
              pageSizeOptions={[10, 25, 50, 100]}
            />
          )}
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <Dialog open={detailsDialogOpen} onOpenChange={setDetailsDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getSeverityBadge(selectedLog?.severity || '')}`}>
                {selectedLog?.severity}
              </span>
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getSourceBadge(selectedLog?.source || '')}`}>
                {selectedLog?.source}
              </span>
              <span>{selectedLog?.error_type}</span>
            </DialogTitle>
            <DialogDescription>
              {selectedLog && formatDateTime(selectedLog.created_at)}
              {selectedLog?.correlation_id && (
                <span className="ml-2 font-mono text-xs">
                  ID: {selectedLog.correlation_id}
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          {selectedLog && (
            <div className="space-y-4 py-4">
              {/* Error Message */}
              <div>
                <h4 className="font-semibold text-sm mb-1">Message</h4>
                <p className="text-sm bg-muted p-3 rounded-lg">{selectedLog.message}</p>
              </div>

              {/* Stack Trace */}
              {selectedLog.stack_trace && (
                <div>
                  <h4 className="font-semibold text-sm mb-1">Stack Trace</h4>
                  <pre className="text-xs bg-muted p-3 rounded-lg overflow-auto max-h-64 whitespace-pre-wrap font-mono">
                    {selectedLog.stack_trace}
                  </pre>
                </div>
              )}

              {/* Request Details */}
              <div className="grid grid-cols-2 gap-4">
                {selectedLog.request_method && (
                  <div>
                    <h4 className="font-semibold text-sm mb-1">Request Method</h4>
                    <p className="text-sm font-mono">{selectedLog.request_method}</p>
                  </div>
                )}
                {selectedLog.request_path && (
                  <div>
                    <h4 className="font-semibold text-sm mb-1">Request Path</h4>
                    <p className="text-sm font-mono break-all">{selectedLog.request_path}</p>
                  </div>
                )}
                {selectedLog.response_status && (
                  <div>
                    <h4 className="font-semibold text-sm mb-1">Response Status</h4>
                    <p className="text-sm font-mono">{selectedLog.response_status}</p>
                  </div>
                )}
                {selectedLog.ip_address && (
                  <div>
                    <h4 className="font-semibold text-sm mb-1">IP Address</h4>
                    <p className="text-sm font-mono">{selectedLog.ip_address}</p>
                  </div>
                )}
              </div>

              {/* User Details */}
              {(selectedLog.user_name || selectedLog.user_email) && (
                <div>
                  <h4 className="font-semibold text-sm mb-1">User</h4>
                  <p className="text-sm">
                    {selectedLog.user_name || 'Unknown'}
                    {selectedLog.user_email && ` (${selectedLog.user_email})`}
                  </p>
                </div>
              )}

              {/* Component (Frontend errors) */}
              {selectedLog.component_name && (
                <div>
                  <h4 className="font-semibold text-sm mb-1">Component</h4>
                  <p className="text-sm font-mono">{selectedLog.component_name}</p>
                </div>
              )}

              {/* Browser Info (Frontend errors) */}
              {selectedLog.browser_info && (
                <div>
                  <h4 className="font-semibold text-sm mb-1">Browser Info</h4>
                  <pre className="text-xs bg-muted p-3 rounded-lg overflow-auto font-mono">
                    {JSON.stringify(JSON.parse(selectedLog.browser_info), null, 2)}
                  </pre>
                </div>
              )}

              {/* User Agent */}
              {selectedLog.user_agent && (
                <div>
                  <h4 className="font-semibold text-sm mb-1">User Agent</h4>
                  <p className="text-xs text-muted-foreground break-all">{selectedLog.user_agent}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Cleanup Confirmation Dialog */}
      <Dialog open={cleanupDialogOpen} onOpenChange={setCleanupDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cleanup Error Logs</DialogTitle>
            <DialogDescription>
              This will permanently delete error logs older than 30 days.
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCleanupDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => cleanupMutation.mutate(30)}
              disabled={cleanupMutation.isPending}
            >
              {cleanupMutation.isPending ? 'Cleaning up...' : 'Delete Old Logs'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
