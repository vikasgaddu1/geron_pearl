/**
 * Impersonation Banner
 * 
 * Displayed at the top of the page when a super admin is impersonating a tenant.
 * Shows tenant info and provides an exit mechanism.
 */

import { useEffect, useState } from 'react';
import { Eye, X, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ImpersonationState {
  tenantName: string;
  readOnly: boolean;
}

export function ImpersonationBanner() {
  const [impersonation, setImpersonation] = useState<ImpersonationState | null>(null);

  useEffect(() => {
    const tenantName = localStorage.getItem('impersonation_tenant');
    const readOnly = localStorage.getItem('impersonation_read_only') === 'true';
    
    if (tenantName) {
      setImpersonation({ tenantName, readOnly });
    }
  }, []);

  const handleExit = () => {
    // Clear impersonation state
    localStorage.removeItem('auth_token');
    localStorage.removeItem('impersonation_tenant');
    localStorage.removeItem('impersonation_read_only');
    
    // Redirect back to super admin dashboard
    window.location.href = '/admin/dashboard';
  };

  if (!impersonation) {
    return null;
  }

  return (
    <div className="bg-amber-500 text-amber-950 px-4 py-2 flex items-center justify-between sticky top-0 z-[100]">
      <div className="flex items-center gap-3">
        <Eye className="h-5 w-5" />
        <span className="font-medium">
          Viewing as: <strong>{impersonation.tenantName}</strong>
        </span>
        {impersonation.readOnly && (
          <div className="flex items-center gap-1 bg-amber-600/30 px-2 py-0.5 rounded text-sm">
            <AlertTriangle className="h-3 w-3" />
            <span>Read-only mode</span>
          </div>
        )}
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleExit}
        className="text-amber-950 hover:text-amber-950 hover:bg-amber-600/30"
      >
        <X className="h-4 w-4 mr-1" />
        Exit Impersonation
      </Button>
    </div>
  );
}

/**
 * Hook to check if currently in impersonation mode
 */
export function useImpersonation() {
  const [isImpersonating, setIsImpersonating] = useState(false);
  const [isReadOnly, setIsReadOnly] = useState(false);

  useEffect(() => {
    const tenantName = localStorage.getItem('impersonation_tenant');
    const readOnly = localStorage.getItem('impersonation_read_only') === 'true';
    
    setIsImpersonating(!!tenantName);
    setIsReadOnly(readOnly);
  }, []);

  return { isImpersonating, isReadOnly };
}
