/**
 * Super Admin Protected Route
 * 
 * Route guard for super admin pages.
 * Redirects to /admin/login if not authenticated.
 */

import { useEffect, useState, ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { getSuperAdminToken, getSuperAdminMe } from '@/api/endpoints/super-admin';

interface SuperAdminProtectedRouteProps {
  children: ReactNode;
}

export function SuperAdminProtectedRoute({ children }: SuperAdminProtectedRouteProps) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const location = useLocation();

  useEffect(() => {
    const checkAuth = async () => {
      const token = getSuperAdminToken();
      
      if (!token) {
        setIsAuthenticated(false);
        return;
      }

      try {
        // Verify token is valid by calling /me endpoint
        await getSuperAdminMe();
        setIsAuthenticated(true);
      } catch (error) {
        // Token is invalid or expired
        setIsAuthenticated(false);
      }
    };

    checkAuth();
  }, []);

  // Show loading state while checking authentication
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-amber-500 mx-auto" />
          <p className="text-slate-400 mt-2">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
