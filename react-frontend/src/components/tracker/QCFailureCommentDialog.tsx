import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, MessageSquare } from 'lucide-react'
import { toast } from 'sonner'
import { trackerApi } from '@/api'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { getErrorMessage } from '@/lib/utils'

interface QCFailureCommentDialogProps {
  trackerId: number | null
  trackerItemCode?: string
  effortId: number | null
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
}

export function QCFailureCommentDialog({
  trackerId,
  trackerItemCode,
  effortId,
  isOpen,
  onClose,
  onSuccess,
}: QCFailureCommentDialogProps) {
  const [comment, setComment] = useState('')
  const queryClient = useQueryClient()

  const setQCFailedWithComment = useMutation({
    mutationFn: async () => {
      if (!trackerId) throw new Error('No tracker selected')
      return trackerApi.createCommentWithStatus(trackerId, {
        comment_text: comment.trim(),
        qc_status: 'failed',
      })
    },
    onSuccess: () => {
      toast.success('QC status set to Failed with comment')
      queryClient.invalidateQueries({ queryKey: ['trackers', effortId] })
      setComment('')
      onClose()
      onSuccess?.()
    },
    onError: (error) => {
      toast.error(`Failed to update status: ${getErrorMessage(error)}`)
    },
  })

  const handleSubmit = () => {
    if (!comment.trim()) {
      toast.error('Please provide a reason for the QC failure')
      return
    }
    setQCFailedWithComment.mutate()
  }

  const handleClose = () => {
    setComment('')
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            QC Failed - Comment Required
          </DialogTitle>
          <DialogDescription>
            {trackerItemCode 
              ? `You are marking "${trackerItemCode}" as QC Failed.`
              : 'You are marking this item as QC Failed.'}
            {' '}Please provide a reason for the failure.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="failure-reason" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Failure Reason <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="failure-reason"
              placeholder="Describe the issues found during QC review..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="min-h-[120px]"
              autoFocus
            />
            <p className="text-xs text-muted-foreground">
              This comment will be saved and the production team will be notified.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={handleClose}
            disabled={setQCFailedWithComment.isPending}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleSubmit}
            disabled={!comment.trim() || setQCFailedWithComment.isPending}
          >
            {setQCFailedWithComment.isPending ? 'Submitting...' : 'Set QC Failed'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}





