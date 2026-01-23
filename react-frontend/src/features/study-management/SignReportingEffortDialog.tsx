import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileSignature, Check, X, AlertTriangle, Shield, Settings } from 'lucide-react'
import { toast } from 'sonner'
import { reportingEffortsApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
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
import { getErrorMessage, formatDateTime } from '@/lib/utils'

interface SignReportingEffortDialogProps {
  reportingEffort: ReportingEffort | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSignComplete?: (updatedEffort: ReportingEffort) => void
  onSetupSignature?: () => void
}

export function SignReportingEffortDialog({
  reportingEffort,
  open,
  onOpenChange,
  onSignComplete,
  onSetupSignature,
}: SignReportingEffortDialogProps) {
  const queryClient = useQueryClient()
  const [totpCode, setTotpCode] = useState('')
  const [reason, setReason] = useState('')
  const [confirmPermanent, setConfirmPermanent] = useState(false)

  // Check signature readiness
  const { data: readiness, isLoading: loadingReadiness, refetch: refetchReadiness } = useQuery({
    queryKey: ['signature-readiness', reportingEffort?.id],
    queryFn: () => reportingEffort?.id ? reportingEffortsApi.checkSignatureReadiness(reportingEffort.id) : null,
    enabled: !!reportingEffort?.id && open,
  })

  // Sign mutation
  const signMutation = useMutation({
    mutationFn: () => reportingEffortsApi.sign(reportingEffort!.id, totpCode, reason),
    onSuccess: (updatedEffort) => {
      toast.success('Reporting effort signed successfully!')
      queryClient.invalidateQueries({ queryKey: ['reporting-efforts'] })
      queryClient.invalidateQueries({ queryKey: ['studies'] })
      queryClient.invalidateQueries({ queryKey: ['signature-readiness'] })
      onSignComplete?.(updatedEffort)
      handleClose()
    },
    onError: (error) => {
      const message = getErrorMessage(error)
      if (message.includes('locked') || message.includes('lockout')) {
        toast.error(message)
        refetchReadiness()
      } else if (message.includes('Invalid TOTP')) {
        toast.error(message)
        setTotpCode('')
      } else {
        toast.error(`Failed to sign: ${message}`)
      }
    },
  })

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setTotpCode('')
      setReason('')
      setConfirmPermanent(false)
    }
  }, [open])

  const handleClose = () => {
    setTotpCode('')
    setReason('')
    setConfirmPermanent(false)
    onOpenChange(false)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!readiness?.can_sign) {
      toast.error('Cannot sign: Please resolve all blockers first')
      return
    }

    if (totpCode.length !== 6) {
      toast.error('Please enter a valid 6-digit code')
      return
    }

    if (reason.length < 10) {
      toast.error('Please provide a reason (at least 10 characters)')
      return
    }

    if (!confirmPermanent) {
      toast.error('Please confirm you understand this action is permanent')
      return
    }

    signMutation.mutate()
  }

  const canSign = readiness?.can_sign &&
    totpCode.length === 6 &&
    reason.length >= 10 &&
    confirmPermanent

  // If already signed, show info
  if (reportingEffort?.is_signed) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileSignature className="h-5 w-5 text-green-500" />
              Reporting Effort Signed
            </DialogTitle>
            <DialogDescription>
              {reportingEffort.database_release_label}
            </DialogDescription>
          </DialogHeader>

          <Alert className="border-green-500/50 bg-green-500/10">
            <Check className="h-4 w-4 text-green-500" />
            <AlertTitle>Electronically Signed</AlertTitle>
            <AlertDescription className="text-sm mt-2">
              <p><strong>Signed by:</strong> {reportingEffort.signed_by_username}</p>
              <p><strong>Signed at:</strong> {reportingEffort.signed_at ? formatDateTime(reportingEffort.signed_at) : 'N/A'}</p>
              {reportingEffort.signature_reason && (
                <p className="mt-2"><strong>Reason:</strong> {reportingEffort.signature_reason}</p>
              )}
            </AlertDescription>
          </Alert>

          <p className="text-sm text-muted-foreground">
            This reporting effort has been electronically signed and is permanently locked.
            No further modifications can be made.
          </p>

          <DialogFooter>
            <Button onClick={handleClose}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileSignature className="h-5 w-5 text-blue-500" />
            Sign Reporting Effort
          </DialogTitle>
          <DialogDescription>
            {reportingEffort?.database_release_label}
          </DialogDescription>
        </DialogHeader>

        {loadingReadiness ? (
          <div className="py-8 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Precondition Checklist */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Signing Requirements</Label>
              <div className="space-y-2 p-3 bg-muted rounded-lg">
                <ChecklistItem
                  checked={readiness?.has_totp_setup ?? false}
                  label="Signature authentication set up"
                  onSetup={!readiness?.has_totp_setup ? onSetupSignature : undefined}
                />
                <ChecklistItem
                  checked={readiness?.is_responsible ?? false}
                  label="Admin or Study LEAD role"
                />
                <ChecklistItem
                  checked={readiness?.all_items_in_production ?? false}
                  label={`All items in production (${readiness?.items_in_production ?? 0}/${readiness?.total_items ?? 0})`}
                />
                <ChecklistItem
                  checked={!readiness?.is_locked_out}
                  label="Account not locked out"
                  error={readiness?.is_locked_out ? `Locked for ${readiness?.lockout_remaining_minutes} min` : undefined}
                />
              </div>
            </div>

            {/* Blockers Alert */}
            {readiness?.blockers && readiness.blockers.length > 0 && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Cannot Sign</AlertTitle>
                <AlertDescription>
                  <ul className="list-disc list-inside mt-2 text-sm">
                    {readiness.blockers.map((blocker, index) => (
                      <li key={index}>{blocker}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}

            {/* Warning about permanence */}
            <Alert variant="default" className="border-amber-500/50 bg-amber-500/10">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <AlertDescription className="text-sm">
                <strong>This action is permanent.</strong> Once signed, this reporting effort cannot be
                unlocked, modified, or deleted. The signature provides a regulatory-grade audit trail.
              </AlertDescription>
            </Alert>

            {/* Reason */}
            <div className="space-y-2">
              <Label htmlFor="sign-reason">
                Reason / Intent for Signing
                <span className="text-destructive"> *</span>
              </Label>
              <Textarea
                id="sign-reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g., Final sign-off for interim analysis submission. All outputs have been reviewed and verified."
                className="min-h-[80px]"
                minLength={10}
              />
              <p className="text-xs text-muted-foreground">
                Minimum 10 characters. This will be recorded in the audit trail.
              </p>
            </div>

            {/* TOTP Code */}
            <div className="space-y-2">
              <Label htmlFor="totp-code">
                Authenticator Code
                <span className="text-destructive"> *</span>
              </Label>
              <Input
                id="totp-code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ''))}
                placeholder="000000"
                className="text-center text-xl tracking-widest font-mono"
                disabled={!readiness?.has_totp_setup}
              />
            </div>

            {/* Confirmation checkbox */}
            <div className="flex items-start gap-2 p-3 border rounded-lg bg-destructive/5 border-destructive/30">
              <Checkbox
                id="confirm-permanent"
                checked={confirmPermanent}
                onCheckedChange={(checked) => setConfirmPermanent(checked === true)}
                className="mt-0.5"
              />
              <label htmlFor="confirm-permanent" className="text-sm cursor-pointer">
                I understand that signing is <strong>permanent and cannot be reversed</strong>.
                This reporting effort will be locked forever.
              </label>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!canSign || signMutation.isPending}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {signMutation.isPending ? (
                  'Signing...'
                ) : (
                  <>
                    <FileSignature className="mr-2 h-4 w-4" />
                    Sign Reporting Effort
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}

// Helper component for checklist items
function ChecklistItem({
  checked,
  label,
  error,
  onSetup,
}: {
  checked: boolean
  label: string
  error?: string
  onSetup?: () => void
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      {checked ? (
        <Check className="h-4 w-4 text-green-500 flex-shrink-0" />
      ) : (
        <X className="h-4 w-4 text-destructive flex-shrink-0" />
      )}
      <span className={checked ? 'text-foreground' : 'text-destructive'}>
        {label}
      </span>
      {error && <span className="text-xs text-destructive">({error})</span>}
      {onSetup && (
        <Button
          type="button"
          variant="link"
          size="sm"
          className="h-auto p-0 text-xs"
          onClick={onSetup}
        >
          <Settings className="h-3 w-3 mr-1" />
          Set up
        </Button>
      )}
    </div>
  )
}
