import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ProgrammerDashboard } from './ProgrammerDashboard'
import { TrackerDashboard } from './TrackerDashboard'
import { usersApi } from '@/api'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { RefreshCw, User } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

export function Dashboard() {
  const [activeTab, setActiveTab] = useState('programmer')
  const { selectedUserId, setSelectedUserId } = useAuthStore()

  const { data: users = [], refetch: refetchUsers } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.getAll,
  })

  const programmers = users.filter((u) => ['programmer', 'lead', 'analyst'].includes(u.role))
  const selectedUser = users.find((u) => u.id === selectedUserId)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg bg-gradient-to-r from-primary to-purple-600 p-6 text-white">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Dashboard</h1>
            <p className="text-white/80">View assignments and track progress</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 rounded-lg bg-white/15 px-4 py-2">
              <User className="h-4 w-4" />
              <span className="text-sm">View As:</span>
              <Select
                value={selectedUserId?.toString() || 'all'}
                onValueChange={(v) => setSelectedUserId(v === 'all' ? null : Number(v))}
              >
                <SelectTrigger className="w-48 border-0 bg-transparent text-white">
                  <SelectValue placeholder="Select user" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Users</SelectItem>
                  {programmers.map((user) => (
                    <SelectItem key={user.id} value={String(user.id)}>
                      {user.username}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button variant="secondary" size="sm" onClick={() => refetchUsers()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Dashboard Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="programmer">Programmer Dashboard</TabsTrigger>
          <TabsTrigger value="tracker">Tracker Dashboard</TabsTrigger>
        </TabsList>

        <TabsContent value="programmer" className="mt-6">
          <ProgrammerDashboard userId={selectedUserId} userName={selectedUser?.username} />
        </TabsContent>

        <TabsContent value="tracker" className="mt-6">
          <TrackerDashboard />
        </TabsContent>
      </Tabs>
    </div>
  )
}

