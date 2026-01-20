import { useEffect, useRef } from 'react'
import { Outlet } from 'react-router-dom'
import { Navbar } from './Navbar'
import { Sidebar } from './Sidebar'
import { useWebSocket } from '@/hooks/useWebSocket'
import { TooltipProvider } from '@/components/ui/tooltip'
import { useAuth } from '@/hooks/useAuth'
import { OnboardingProvider } from '@/features/onboarding'

export function AppShell() {
  // Initialize WebSocket connection
  useWebSocket()
  
  const { isAuthenticated, fetchStudyRoles } = useAuth()
  const hasFetchedRef = useRef(false)
  
  // Fetch study roles once on mount to ensure fresh data after page refresh
  useEffect(() => {
    if (isAuthenticated && !hasFetchedRef.current) {
      hasFetchedRef.current = true
      fetchStudyRoles()
    }
  }, [isAuthenticated]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <TooltipProvider>
      <OnboardingProvider>
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
      </OnboardingProvider>
    </TooltipProvider>
  )
}










