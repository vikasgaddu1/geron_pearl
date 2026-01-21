import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { MessageSquarePlus, Bug, Lightbulb, Clock, CheckCircle2, Loader2, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from 'sonner'
import { feedbackApi } from '@/api/endpoints/feedback'
import type { FeatureRequest, FeatureRequestCategory, FeatureRequestStatus } from '@/types'
import { formatDateTime } from '@/lib/utils'

const feedbackSchema = z.object({
  category: z.enum(['bug', 'feature'] as const),
  title: z.string().min(1, 'Title is required').max(200, 'Title must be 200 characters or less'),
  description: z.string().min(1, 'Description is required'),
})

type FeedbackFormData = z.infer<typeof feedbackSchema>

function getStatusBadge(status: FeatureRequestStatus) {
  switch (status) {
    case 'pending':
      return (
        <Badge variant="secondary" className="bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
          <Clock className="h-3 w-3 mr-1" />
          Pending
        </Badge>
      )
    case 'working':
      return (
        <Badge variant="default" className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
          In Progress
        </Badge>
      )
    case 'done':
      return (
        <Badge variant="outline" className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-green-300">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          Done
        </Badge>
      )
  }
}

function getCategoryIcon(category: FeatureRequestCategory) {
  switch (category) {
    case 'bug':
      return <Bug className="h-4 w-4 text-red-500" />
    case 'feature':
      return <Lightbulb className="h-4 w-4 text-purple-500" />
  }
}

function RequestCard({ request }: { request: FeatureRequest }) {
  return (
    <Card className="mb-3">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            {getCategoryIcon(request.category)}
            <CardTitle className="text-sm font-medium">{request.title}</CardTitle>
          </div>
          {getStatusBadge(request.status)}
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Submitted {formatDateTime(request.created_at)}
        </p>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-sm text-muted-foreground line-clamp-2">{request.description}</p>
        {request.admin_response && (
          <div className="mt-3 p-2 bg-muted rounded-md">
            <p className="text-xs font-medium text-foreground mb-1">Response:</p>
            <p className="text-sm">{request.admin_response}</p>
            {request.responded_at && (
              <p className="text-xs text-muted-foreground mt-1">
                {formatDateTime(request.responded_at)}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function FeedbackDialog() {
  const [open, setOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('submit')
  const queryClient = useQueryClient()

  const form = useForm<FeedbackFormData>({
    resolver: zodResolver(feedbackSchema),
    defaultValues: {
      category: 'feature',
      title: '',
      description: '',
    },
  })

  // Fetch user's requests when dialog is open
  const { data: myRequests, isLoading: isLoadingRequests } = useQuery({
    queryKey: ['myFeedbackRequests'],
    queryFn: () => feedbackApi.getMyRequests(),
    enabled: open && activeTab === 'history',
  })

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: feedbackApi.submit,
    onSuccess: () => {
      toast.success('Feedback submitted successfully!')
      form.reset()
      queryClient.invalidateQueries({ queryKey: ['myFeedbackRequests'] })
      setActiveTab('history')
    },
    onError: () => {
      toast.error('Failed to submit feedback. Please try again.')
    },
  })

  const onSubmit = (data: FeedbackFormData) => {
    submitMutation.mutate(data)
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" title="Submit Feedback">
          <MessageSquarePlus className="h-5 w-5" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Feedback</DialogTitle>
          <DialogDescription>
            Submit a feature request or report a bug. We value your input!
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-2">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="submit">Submit</TabsTrigger>
            <TabsTrigger value="history">My Requests</TabsTrigger>
          </TabsList>

          <TabsContent value="submit" className="mt-4">
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Select
                  value={form.watch('category')}
                  onValueChange={(value: FeatureRequestCategory) => form.setValue('category', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="feature">
                      <div className="flex items-center gap-2">
                        <Lightbulb className="h-4 w-4 text-purple-500" />
                        Feature Request
                      </div>
                    </SelectItem>
                    <SelectItem value="bug">
                      <div className="flex items-center gap-2">
                        <Bug className="h-4 w-4 text-red-500" />
                        Bug Report
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                {form.formState.errors.category && (
                  <p className="text-sm text-red-500">{form.formState.errors.category.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  placeholder="Brief summary of your request"
                  {...form.register('title')}
                />
                {form.formState.errors.title && (
                  <p className="text-sm text-red-500">{form.formState.errors.title.message}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Please provide details..."
                  rows={4}
                  {...form.register('description')}
                />
                {form.formState.errors.description && (
                  <p className="text-sm text-red-500">{form.formState.errors.description.message}</p>
                )}
              </div>

              <Button type="submit" className="w-full" disabled={submitMutation.isPending}>
                {submitMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4 mr-2" />
                    Submit Feedback
                  </>
                )}
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="history" className="mt-4">
            {isLoadingRequests ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : !myRequests || myRequests.length === 0 ? (
              <div className="text-center py-8">
                <MessageSquarePlus className="h-12 w-12 mx-auto text-muted-foreground/30" />
                <p className="mt-2 text-sm text-muted-foreground">No feedback submitted yet</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Your submissions will appear here
                </p>
              </div>
            ) : (
              <ScrollArea className="h-[300px] pr-4">
                {myRequests.map((request) => (
                  <RequestCard key={request.id} request={request} />
                ))}
              </ScrollArea>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
