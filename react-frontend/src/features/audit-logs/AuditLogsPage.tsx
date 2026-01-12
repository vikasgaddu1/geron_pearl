import { useState, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { FileText, RefreshCw, Eye } from 'lucide-react'
import { auditLogsApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { DataTable, ColumnDef } from '@/components/common/DataTable'
import { TooltipWrapper } from '@/components/common/TooltipWrapper'
import { HelpIcon } from '@/components/common/HelpIcon'
import type { AuditLog } from '@/types'
import { formatDateTime } from '@/lib/utils'

export function AuditLogsPage() {
  const queryClient = useQueryClient()
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false)
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)

  // Query
  const { data: auditLogs = [], isLoading } = useQuery({
    queryKey: ['auditLogs'],
    queryFn: () => auditLogsApi.getAll({ limit: 500 }),
  })

  // Refresh function
  const refetch = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['auditLogs'] })
  }, [queryClient])

  // View details handler
  const handleViewDetails = (log: AuditLog) => {
    setSelectedLog(log)
    setDetailsDialogOpen(true)
  }

  // Format changes JSON for display
  const formatChanges = (changesJson: string | undefined): React.ReactNode => {
    if (!changesJson) return <span className="text-muted-foreground">No changes recorded</span>

    try {
      const changes = JSON.parse(changesJson)
      return (
        <pre className="text-sm bg-muted p-4 rounded-lg overflow-auto max-h-96">
          {JSON.stringify(changes, null, 2)}
        </pre>
      )
    } catch {
      return <span className="text-muted-foreground">{changesJson}</span>
    }
  }

  // Get action badge style
  const getActionBadge = (action: string) => {
    const styles: Record<string, string> = {
      CREATE: 'bg-green-100 text-green-800 border-green-200',
      UPDATE: 'bg-blue-100 text-blue-800 border-blue-200',
      DELETE: 'bg-red-100 text-red-800 border-red-200',
    }
    return styles[action] || 'bg-gray-100 text-gray-800 border-gray-200'
  }

  // Format table name for display
  const formatTableName = (tableName: string): string => {
    return tableName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  // Get unique table names for filter options
  const tableNames = [...new Set(auditLogs.map(log => log.table_name))].sort()

  // Define table columns
  const columns: ColumnDef<AuditLog>[] = [
    {
      id: 'created_at',
      header: 'Date & Time',
      accessorKey: 'created_at',
      filterType: 'date',
      helpText: 'When the action was performed.',
      cell: (value) => (
        <span className="text-sm whitespace-nowrap">{formatDateTime(value)}</span>
      ),
    },
    {
      id: 'action',
      header: 'Action',
      accessorKey: 'action',
      filterType: 'select',
      filterOptions: ['CREATE', 'UPDATE', 'DELETE'],
      helpText: 'Type of operation: CREATE, UPDATE, or DELETE.',
      cell: (value) => (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getActionBadge(value)}`}>
          {value}
        </span>
      ),
    },
    {
      id: 'table_name',
      header: 'Entity Type',
      accessorKey: 'table_name',
      filterType: 'select',
      filterOptions: tableNames,
      helpText: 'The type of entity that was modified.',
      cell: (value) => (
        <span className="font-medium">{formatTableName(value)}</span>
      ),
    },
    {
      id: 'record_id',
      header: 'Record ID',
      accessorKey: 'record_id',
      filterType: 'text',
      helpText: 'The ID of the record that was modified.',
      cell: (value) => (
        <span className="font-mono text-sm">{value}</span>
      ),
    },
    {
      id: 'user_name',
      header: 'User',
      accessorKey: 'user_name',
      filterType: 'text',
      helpText: 'The user who performed the action.',
      cell: (value, row) => (
        <div>
          <div className="font-medium">{value || 'System'}</div>
          {row.user_email && (
            <div className="text-xs text-muted-foreground">{row.user_email}</div>
          )}
        </div>
      ),
    },
    {
      id: 'ip_address',
      header: 'IP Address',
      accessorKey: 'ip_address',
      filterType: 'text',
      helpText: 'The IP address from which the action was performed.',
      cell: (value) => (
        <span className="font-mono text-sm">{value || '-'}</span>
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
          <TooltipWrapper content="View change details">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleViewDetails(log)}
              disabled={!log.changes_json}
            >
              <Eye className="h-4 w-4" />
            </Button>
          </TooltipWrapper>
        </div>
      ),
    },
  ]

  if (isLoading) {
    return <PageLoader text="Loading audit logs..." />
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div className="flex items-center gap-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Audit Logs
              </CardTitle>
              <CardDescription>
                View system activity and change history
              </CardDescription>
            </div>
            <HelpIcon
              title="Audit Logs"
              content={
                <div className="space-y-2">
                  <p>Track all changes made to the system, including who made them and when.</p>
                  <div className="space-y-1">
                    <p className="font-semibold text-sm">Action Types:</p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li><strong>CREATE:</strong> A new record was added</li>
                      <li><strong>UPDATE:</strong> An existing record was modified</li>
                      <li><strong>DELETE:</strong> A record was removed</li>
                    </ul>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Click the eye icon to view detailed changes for each entry.
                  </p>
                </div>
              }
            />
          </div>
          <div className="flex gap-2">
            <TooltipWrapper content="Refresh audit logs">
              <Button variant="outline" size="sm" onClick={refetch}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </TooltipWrapper>
          </div>
        </CardHeader>
        <CardContent>
          {auditLogs.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No audit logs found"
              description="System activity will appear here as changes are made."
            />
          ) : (
            <DataTable
              data={auditLogs}
              columns={columns}
              defaultPageSize={25}
              pageSizeOptions={[10, 25, 50, 100]}
            />
          )}
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <Dialog open={detailsDialogOpen} onOpenChange={setDetailsDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Change Details</DialogTitle>
            <DialogDescription>
              {selectedLog && (
                <span>
                  {selectedLog.action} on {formatTableName(selectedLog.table_name)} (ID: {selectedLog.record_id})
                  <br />
                  <span className="text-xs">
                    By {selectedLog.user_name || 'System'} at {formatDateTime(selectedLog.created_at)}
                  </span>
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            {formatChanges(selectedLog?.changes_json)}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
