import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Lock, Unlock, AlertTriangle, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'
import { reportingEffortsApi, trackerApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import type { ReportingEffort } from '@/types'
import { getErrorMessage } from '@/lib/utils'

interface LockReportingEffortDialogProps {
  reportingEffort: ReportingEffort | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function LockReportingEffortDialog({
  reportingEffort,
  open,
  onOpenChange,
}: LockReportingEffortDialogProps) {
  const queryClient = useQueryClient()
  const [reason, setReason] = useState('')
  const [confirmNotInProduction, setConfirmNotInProduction] = useState(false)

  const isLocking = !reportingEffort?.is_locked

  // Fetch trackers for the reporting effort when locking
  const { data: trackers = [] } = useQuery({
    queryKey: ['trackers', reportingEffort?.id],
    queryFn: () => reportingEffort?.id ? trackerApi.getByEffortBulk(reportingEffort.id) : Promise.resolve([]),
    enabled: !!reportingEffort?.id && open && isLocking,
  })

  // Find items that are not in production
  const itemsNotInProduction = trackers.filter(t => !t.in_production_flag)
  const hasItemsNotInProduction = itemsNotInProduction.length > 0

  const lockMutation = useMutation({
    mutationFn: () => reportingEffortsApi.lock(reportingEffort!.id, reason),
    onSuccess: () => {
      toast.success('Reporting effort locked successfully')
      queryClient.invalidateQueries({ queryKey: ['reporting-efforts'] })
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      queryClient.invalidateQueries({ queryKey: ['trackers'] })
      handleClose()
    },
    onError: (error) => {
      toast.error(`Failed to lock: ${getErrorMessage(error)}`)
    },
  })

  const unlockMutation = useMutation({
    mutationFn: () => reportingEffortsApi.unlock(reportingEffort!.id, reason),
    onSuccess: () => {
      toast.success('Reporting effort unlocked successfully')
      queryClient.invalidateQueries({ queryKey: ['reporting-efforts'] })
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      queryClient.invalidateQueries({ queryKey: ['trackers'] })
      handleClose()
    },
    onError: (error) => {
      toast.error(`Failed to unlock: ${getErrorMessage(error)}`)
    },
  })

  const handleClose = () => {
    setReason('')
    setConfirmNotInProduction(false)
    onOpenChange(false)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!reason.trim()) {
      toast.error('Please provide a reason')
      return
    }
    if (isLocking) {
      lockMutation.mutate()
    } else {
      unlockMutation.mutate()
    }
  }

  const isSubmitting = lockMutation.isPending || unlockMutation.isPending
  const canSubmitLock = !hasItemsNotInProduction || confirmNotInProduction

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isLocking ? (
              <>
                <Lock className="h-5 w-5 text-amber-500" />
                Lock Reporting Effort
              </>
            ) : (
              <>
                <Unlock className="h-5 w-5 text-green-500" />
                Unlock Reporting Effort
              </>
            )}
          </DialogTitle>
          <DialogDescription>
            {reportingEffort?.database_release_label}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isLocking && (
            <Alert variant="default" className="border-amber-500/50 bg-amber-500/10">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <AlertDescription className="text-sm">
                Locking this reporting effort will prevent:
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>Creating, editing, or deleting items</li>
                  <li>Updating tracker assignments and statuses</li>
                  <li>Adding or resolving comments</li>
                  <li>Any modifications to phases and milestones</li>
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {/* Warning for items not in production */}
          {isLocking && hasItemsNotInProduction && (
            <Alert variant="destructive" className="border-red-500/50">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle className="text-sm font-semibold">
                {itemsNotInProduction.length} item(s) not in production
              </AlertTitle>
              <AlertDescription className="text-sm mt-2">
                <p className="mb-2">The following items do not have the "In Production" flag set:</p>
                <ScrollArea className="max-h-32 border rounded p-2 bg-background/50">
                  <ul className="space-y-1 text-xs">
                    {itemsNotInProduction.map(item => (
                      <li key={item.id} className="flex items-center gap-2">
                        <span className="font-mono">{item.item_code}</span>
                        {item.item_title && (
                          <span className="text-muted-foreground truncate">- {item.item_title}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </ScrollArea>
                <div className="flex items-center gap-2 mt-3">
                  <Checkbox
                    id="confirm-not-in-production"
                    checked={confirmNotInProduction}
                    onCheckedChange={(checked) => setConfirmNotInProduction(checked === true)}
                  />
                  <label
                    htmlFor="confirm-not-in-production"
                    className="text-xs cursor-pointer"
                  >
                    I understand and want to lock anyway
                  </label>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {!isLocking && reportingEffort?.lock_reason && (
            <Alert variant="default" className="border-blue-500/50 bg-blue-500/10">
              <Lock className="h-4 w-4 text-blue-500" />
              <AlertDescription className="text-sm">
                <span className="font-medium">Current lock reason:</span>
                <p className="mt-1 text-muted-foreground">{reportingEffort.lock_reason}</p>
                {reportingEffort.locked_by_username && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Locked by {reportingEffort.locked_by_username}
                    {reportingEffort.locked_at && (
                      <> on {new Date(reportingEffort.locked_at).toLocaleDateString()}</>
                    )}
                  </p>
                )}
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="reason">
              {isLocking ? 'Reason for locking' : 'Reason for unlocking'}
              <span className="text-destructive"> *</span>
            </Label>
            <Textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={
                isLocking
                  ? 'e.g., Data freeze for interim analysis'
                  : 'e.g., Corrections needed for final review'
              }
              className="min-h-[100px]"
              required
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || !reason.trim() || (isLocking && !canSubmitLock)}
              variant={isLocking ? 'default' : 'default'}
              className={isLocking ? 'bg-amber-600 hover:bg-amber-700' : 'bg-green-600 hover:bg-green-700'}
            >
              {isSubmitting ? (
                isLocking ? 'Locking...' : 'Unlocking...'
              ) : (
                <>
                  {isLocking ? (
                    <>
                      <Lock className="mr-2 h-4 w-4" />
                      Lock Reporting Effort
                    </>
                  ) : (
                    <>
                      <Unlock className="mr-2 h-4 w-4" />
                      Unlock Reporting Effort
                    </>
                  )}
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
