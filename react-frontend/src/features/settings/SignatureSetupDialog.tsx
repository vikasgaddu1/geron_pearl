import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { QRCodeSVG } from 'qrcode.react'
import { Shield, Copy, Check, RefreshCw, AlertTriangle, KeyRound } from 'lucide-react'
import { toast } from 'sonner'
import { usersApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { getErrorMessage } from '@/lib/utils'

interface SignatureSetupDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

type SetupStep = 'loading' | 'scan' | 'verify' | 'complete'

export function SignatureSetupDialog({
  open,
  onOpenChange,
}: SignatureSetupDialogProps) {
  const queryClient = useQueryClient()
  const [step, setStep] = useState<SetupStep>('loading')
  const [provisioningUri, setProvisioningUri] = useState<string>('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [totpCode, setTotpCode] = useState('')
  const [copiedCodes, setCopiedCodes] = useState(false)

  // Check current status when dialog opens
  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ['signature-status'],
    queryFn: usersApi.getSignatureStatus,
    enabled: open,
  })

  // Setup mutation
  const setupMutation = useMutation({
    mutationFn: usersApi.setupSignature,
    onSuccess: (data) => {
      setProvisioningUri(data.provisioning_uri)
      setBackupCodes(data.backup_codes)
      setStep('scan')
    },
    onError: (error) => {
      toast.error(`Setup failed: ${getErrorMessage(error)}`)
    },
  })

  // Verify mutation
  const verifyMutation = useMutation({
    mutationFn: (code: string) => usersApi.verifySignatureSetup(code),
    onSuccess: () => {
      toast.success('Signature authentication setup complete!')
      setStep('complete')
      queryClient.invalidateQueries({ queryKey: ['signature-status'] })
    },
    onError: (error) => {
      toast.error(`Verification failed: ${getErrorMessage(error)}`)
      setTotpCode('')
    },
  })

  // Reset mutation
  const resetMutation = useMutation({
    mutationFn: usersApi.resetSignature,
    onSuccess: (data) => {
      setProvisioningUri(data.provisioning_uri)
      setBackupCodes(data.backup_codes)
      setStep('scan')
      toast.success('Previous authenticator revoked. Please set up again.')
    },
    onError: (error) => {
      toast.error(`Reset failed: ${getErrorMessage(error)}`)
    },
  })

  // Initialize on open
  useEffect(() => {
    if (open) {
      setTotpCode('')
      setCopiedCodes(false)
      if (status?.is_setup_completed) {
        // Already set up, show reset option
        setStep('complete')
      } else {
        // Start fresh setup
        setStep('loading')
        setupMutation.mutate()
      }
    }
  }, [open, status?.is_setup_completed])

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault()
    if (totpCode.length !== 6) {
      toast.error('Please enter a 6-digit code')
      return
    }
    verifyMutation.mutate(totpCode)
  }

  const handleCopyBackupCodes = () => {
    const codesText = backupCodes.join('\n')
    navigator.clipboard.writeText(codesText)
    setCopiedCodes(true)
    toast.success('Backup codes copied to clipboard')
    // Don't reset copiedCodes - keep the button enabled so user can proceed
  }

  const handleReset = () => {
    if (confirm('Are you sure you want to reset your signature authentication? You will need to reconfigure your authenticator app.')) {
      resetMutation.mutate()
    }
  }

  const handleClose = () => {
    setTotpCode('')
    setCopiedCodes(false)
    onOpenChange(false)
  }

  const handleProceedToVerify = () => {
    if (!copiedCodes) {
      toast.warning('Please save your backup codes before proceeding')
      return
    }
    setStep('verify')
  }

  const isLoading = setupMutation.isPending || verifyMutation.isPending || resetMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-500" />
            Signature Authentication Setup
          </DialogTitle>
          <DialogDescription>
            Set up two-factor authentication for electronic signatures
          </DialogDescription>
        </DialogHeader>

        {step === 'loading' && (
          <div className="py-8 flex flex-col items-center justify-center gap-4">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Generating secure key...</p>
          </div>
        )}

        {step === 'scan' && (
          <div className="space-y-4">
            <Alert className="border-blue-500/50 bg-blue-500/10">
              <KeyRound className="h-4 w-4 text-blue-500" />
              <AlertDescription className="text-sm">
                Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
              </AlertDescription>
            </Alert>

            {/* QR Code */}
            <div className="flex justify-center py-4 bg-white rounded-lg">
              <QRCodeSVG
                value={provisioningUri}
                size={200}
                level="M"
                includeMargin
              />
            </div>

            {/* Backup Codes */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                Backup Codes (save these securely)
              </Label>
              <div className="grid grid-cols-2 gap-2 p-3 bg-muted rounded-lg font-mono text-sm">
                {backupCodes.map((code, index) => (
                  <div key={index} className="text-center py-1">
                    {code}
                  </div>
                ))}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyBackupCodes}
                className="w-full"
              >
                {copiedCodes ? (
                  <>
                    <Check className="mr-2 h-4 w-4 text-green-500" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="mr-2 h-4 w-4" />
                    Copy Backup Codes
                  </>
                )}
              </Button>
              <p className="text-xs text-muted-foreground text-center">
                Each backup code can only be used once. Keep them safe for emergency access.
              </p>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleProceedToVerify} disabled={!copiedCodes}>
                Continue to Verification
              </Button>
            </DialogFooter>
          </div>
        )}

        {step === 'verify' && (
          <form onSubmit={handleVerify} className="space-y-4">
            <Alert className="border-blue-500/50 bg-blue-500/10">
              <Shield className="h-4 w-4 text-blue-500" />
              <AlertDescription className="text-sm">
                Enter the 6-digit code from your authenticator app to complete setup
              </AlertDescription>
            </Alert>

            <div className="space-y-2">
              <Label htmlFor="totp-code">Verification Code</Label>
              <Input
                id="totp-code"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ''))}
                placeholder="000000"
                className="text-center text-2xl tracking-widest font-mono"
                autoFocus
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setStep('scan')}>
                Back
              </Button>
              <Button type="submit" disabled={isLoading || totpCode.length !== 6}>
                {verifyMutation.isPending ? 'Verifying...' : 'Verify & Complete'}
              </Button>
            </DialogFooter>
          </form>
        )}

        {step === 'complete' && (
          <div className="space-y-4">
            <Alert className="border-green-500/50 bg-green-500/10">
              <Check className="h-4 w-4 text-green-500" />
              <AlertDescription className="text-sm">
                Signature authentication is set up and active. You can now electronically sign reporting efforts.
              </AlertDescription>
            </Alert>

            <div className="p-4 bg-muted rounded-lg space-y-2">
              <p className="text-sm font-medium">What you can do now:</p>
              <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
                <li>Sign reporting efforts when all items are in production</li>
                <li>Signatures are permanent and provide regulatory-grade sign-off</li>
                <li>Use backup codes if you lose access to your authenticator</li>
              </ul>
            </div>

            <DialogFooter className="flex-col sm:flex-row gap-2">
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={resetMutation.isPending}
                className="text-destructive hover:text-destructive"
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${resetMutation.isPending ? 'animate-spin' : ''}`} />
                Reset Authenticator
              </Button>
              <Button onClick={handleClose}>
                Done
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
