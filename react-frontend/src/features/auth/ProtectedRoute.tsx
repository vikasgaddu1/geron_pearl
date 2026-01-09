import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { PageLoader } from '@/components/common/LoadingSpinner'

interface ProtectedRouteProps {
  children: React.ReactNode
  /** Require global admin access only */
  requireAdmin?: boolean
  /** Allow access for global admin OR users with LEAD role in at least one study */
  requireAdminOrLead?: boolean
}

export function ProtectedRoute({ children, requireAdmin, requireAdminOrLead }: ProtectedRouteProps) {
  const { isAuthenticated, currentUser, isLoading, hasLeadAccess } = useAuthStore()
  const location = useLocation()

  // Show loading spinner while checking auth state
  if (isLoading) {
    return <PageLoader text="Checking authentication..." />
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !currentUser) {
    // Save the location they were trying to access
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check admin-only access if required
  if (requireAdmin && !currentUser.is_admin) {
    // User doesn't have admin permissions
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-destructive">403</h1>
          <p className="text-xl text-muted-foreground">Access Denied</p>
          <p className="text-sm text-muted-foreground">
            You don't have permission to access this page.
            <br />
            Administrator access required.
          </p>
        </div>
      </div>
    )
  }

  // Check admin or LEAD access if required
  if (requireAdminOrLead) {
    const hasAccess = currentUser.is_admin || hasLeadAccess()
    if (!hasAccess) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center space-y-4">
            <h1 className="text-4xl font-bold text-destructive">403</h1>
            <p className="text-xl text-muted-foreground">Access Denied</p>
            <p className="text-sm text-muted-foreground">
              You don't have permission to access this page.
              <br />
              Administrator or Study Lead access required.
            </p>
          </div>
        </div>
      )
    }
  }

  // User is authenticated and has sufficient permissions
  return <>{children}</>
}




