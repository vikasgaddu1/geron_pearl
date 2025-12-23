import { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { PageLoader } from '@/components/common/LoadingSpinner'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: 'ADMIN' | 'EDITOR' | 'VIEWER'
}

export function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { isAuthenticated, currentUser, isLoading } = useAuthStore()
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

  // Check role-based access if required
  if (requiredRole) {
    const userRole = currentUser.role
    
    // Role hierarchy: ADMIN > EDITOR > VIEWER
    const roleHierarchy = {
      ADMIN: 3,
      EDITOR: 2,
      VIEWER: 1,
    }
    
    const userRoleLevel = roleHierarchy[userRole as keyof typeof roleHierarchy] || 0
    const requiredRoleLevel = roleHierarchy[requiredRole]
    
    if (userRoleLevel < requiredRoleLevel) {
      // User doesn't have sufficient permissions
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center space-y-4">
            <h1 className="text-4xl font-bold text-destructive">403</h1>
            <p className="text-xl text-muted-foreground">Access Denied</p>
            <p className="text-sm text-muted-foreground">
              You don't have permission to access this page.
              <br />
              Required role: {requiredRole}
            </p>
          </div>
        </div>
      )
    }
  }

  // User is authenticated and has sufficient permissions
  return <>{children}</>
}

