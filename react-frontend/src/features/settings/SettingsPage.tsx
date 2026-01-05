import { useState, useEffect } from 'react'
import { Settings, Save, RefreshCw, User, Clock } from 'lucide-react'
import { toast } from 'sonner'
import { useAppSettings, useUpdateSettings } from '@/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { PageLoader } from '@/components/common/LoadingSpinner'
import { HelpIcon } from '@/components/common/HelpIcon'
import { getErrorMessage, formatDateTime } from '@/lib/utils'

export function SettingsPage() {
  const { data: settings, isLoading, refetch } = useAppSettings()
  const updateSettings = useUpdateSettings()

  const [dueDateOffset, setDueDateOffset] = useState<number>(7)
  const [hasChanges, setHasChanges] = useState(false)

  // Sync local state with fetched settings
  useEffect(() => {
    if (settings) {
      setDueDateOffset(settings.default_due_date_offset)
      setHasChanges(false)
    }
  }, [settings])

  // Track changes
  useEffect(() => {
    if (settings) {
      setHasChanges(dueDateOffset !== settings.default_due_date_offset)
    }
  }, [dueDateOffset, settings])

  const handleSave = async () => {
    if (!hasChanges) return

    try {
      await updateSettings.mutateAsync({
        default_due_date_offset: dueDateOffset,
      })
      toast.success('Settings saved successfully')
    } catch (error) {
      toast.error(`Failed to save settings: ${getErrorMessage(error)}`)
    }
  }

  const handleReset = () => {
    if (settings) {
      setDueDateOffset(settings.default_due_date_offset)
    }
  }

  if (isLoading) {
    return <PageLoader text="Loading settings..." />
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Settings className="h-6 w-6 text-primary" />
            Application Settings
          </h1>
          <p className="text-muted-foreground mt-1">
            Configure application-wide settings. Changes take effect immediately.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            disabled={updateSettings.isPending}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            Due Date Settings
          </CardTitle>
          <CardDescription>
            Configure default values for tracker due dates
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Label htmlFor="due-date-offset">Default Due Date Offset</Label>
              <HelpIcon content="When a production programmer is assigned to a tracker without an existing due date, the due date will automatically be set to today plus this number of days." />
            </div>
            <div className="flex items-center gap-4">
              <Input
                id="due-date-offset"
                type="number"
                min={1}
                max={365}
                value={dueDateOffset}
                onChange={(e) => setDueDateOffset(parseInt(e.target.value) || 1)}
                className="w-24"
              />
              <span className="text-muted-foreground">days</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Valid range: 1 to 365 days. Current setting: {settings?.default_due_date_offset || 7} days.
            </p>
          </div>

          <div className="flex items-center justify-between pt-4 border-t">
            <div className="text-sm text-muted-foreground">
              {settings?.updated_by_username && (
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Last updated by {settings.updated_by_username} on{' '}
                  {formatDateTime(settings.updated_at)}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              {hasChanges && (
                <Button variant="outline" onClick={handleReset}>
                  Reset
                </Button>
              )}
              <Button
                onClick={handleSave}
                disabled={!hasChanges || updateSettings.isPending}
              >
                {updateSettings.isPending ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Placeholder for future settings sections */}
      <Card className="opacity-50">
        <CardHeader>
          <CardTitle className="text-muted-foreground">More Settings Coming Soon</CardTitle>
          <CardDescription>
            Additional configuration options will be added here in future updates.
          </CardDescription>
        </CardHeader>
      </Card>
    </div>
  )
}
