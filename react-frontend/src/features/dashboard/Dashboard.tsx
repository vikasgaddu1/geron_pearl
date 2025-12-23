import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ProgrammerDashboard } from './ProgrammerDashboard'
import { TrackerDashboard } from './TrackerDashboard'
import { useAuthStore } from '@/stores/authStore'

export function Dashboard() {
  const [activeTab, setActiveTab] = useState('programmer')
  const { currentUser } = useAuthStore()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg bg-gradient-to-r from-primary to-purple-600 p-6 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-white/80">
              {currentUser ? `Welcome back, ${currentUser.username}!` : 'View assignments and track progress'}
            </p>
          </div>
        </div>
      </div>

      {/* Dashboard Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="programmer">My Dashboard</TabsTrigger>
          <TabsTrigger value="tracker">Tracker Dashboard</TabsTrigger>
        </TabsList>

        <TabsContent value="programmer" className="mt-6">
          <ProgrammerDashboard />
        </TabsContent>

        <TabsContent value="tracker" className="mt-6">
          <TrackerDashboard />
        </TabsContent>
      </Tabs>
    </div>
  )
}

