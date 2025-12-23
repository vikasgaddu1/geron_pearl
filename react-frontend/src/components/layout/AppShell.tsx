import { Outlet } from 'react-router-dom'
import { Navbar } from './Navbar'
import { Sidebar } from './Sidebar'
import { useWebSocket } from '@/hooks/useWebSocket'
import { TooltipProvider } from '@/components/ui/tooltip'

export function AppShell() {
  // Initialize WebSocket connection
  useWebSocket()

  return (
    <TooltipProvider>
      <div className="flex min-h-screen flex-col">
        <Navbar />
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 overflow-auto">
            <div className="container mx-auto p-6">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </TooltipProvider>
  )
}

