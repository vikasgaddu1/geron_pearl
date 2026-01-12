import { useQuery } from '@tanstack/react-query'
import { History, Lock, Unlock } from 'lucide-react'
import { reportingEffortsApi } from '@/api'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
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
import { PageLoader } from '@/components/common/LoadingSpinner'
import type { ReportingEffort, LockHistoryEntry } from '@/types'
import { cn } from '@/lib/utils'

interface LockHistoryDialogProps {
  reportingEffort: ReportingEffort | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function ActionBadge({ action }: { action: 'LOCK' | 'UNLOCK' }) {
  const isLock = action === 'LOCK'
  return (
    <Badge
      variant="outline"
      className={cn(
        'gap-1',
        isLock
          ? 'bg-amber-500/15 text-amber-600 border-amber-500/30'
          : 'bg-green-500/15 text-green-600 border-green-500/30'
      )}
    >
      {isLock ? <Lock className="h-3 w-3" /> : <Unlock className="h-3 w-3" />}
      {isLock ? 'Locked' : 'Unlocked'}
    </Badge>
  )
}

export function LockHistoryDialog({
  reportingEffort,
  open,
  onOpenChange,
}: LockHistoryDialogProps) {
  const { data: history, isLoading } = useQuery({
    queryKey: ['lock-history', reportingEffort?.id],
    queryFn: () => reportingEffortsApi.getLockHistory(reportingEffort!.id),
    enabled: !!reportingEffort && open,
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <History className="h-5 w-5 text-muted-foreground" />
            Lock History
          </DialogTitle>
          <DialogDescription>
            {reportingEffort?.database_release_label}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <PageLoader message="Loading history..." />
        ) : !history || history.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            No lock history found for this reporting effort.
          </div>
        ) : (
          <ScrollArea className="max-h-[400px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[120px]">Action</TableHead>
                  <TableHead className="w-[180px]">Date</TableHead>
                  <TableHead className="w-[120px]">Performed By</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((entry: LockHistoryEntry) => (
                  <TableRow key={entry.id}>
                    <TableCell>
                      <ActionBadge action={entry.action} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(entry.created_at)}
                    </TableCell>
                    <TableCell className="font-medium">
                      {entry.performed_by_username}
                    </TableCell>
                    <TableCell className="text-sm">
                      {entry.reason}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollArea>
        )}

        <div className="flex justify-end mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
