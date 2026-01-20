/**
 * Impersonation Banner
 * 
 * Displayed at the top of the page when a super admin is impersonating a tenant.
 * Shows tenant info and provides an exit mechanism.
 */

import { useEffect, useState } from 'react';
import { Eye, X, AlertTriangle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { endImpersonation } from '@/api/endpoints/super-admin';

interface ImpersonationState {
  tenantName: string;
  tenantId: number | null;
  readOnly: boolean;
}

export function ImpersonationBanner() {
  const [impersonation, setImpersonation] = useState<ImpersonationState | null>(null);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const tenantName = localStorage.getItem('impersonation_tenant');
    const tenantIdStr = localStorage.getItem('impersonation_tenant_id');
    const readOnly = localStorage.getItem('impersonation_read_only') === 'true';
    
    if (tenantName) {
      setImpersonation({ 
        tenantName, 
        tenantId: tenantIdStr ? parseInt(tenantIdStr, 10) : null,
        readOnly 
      });
    }
  }, []);

  const handleExit = async () => {
    setExiting(true);
    
    try {
      // Call backend to log impersonation end (for audit trail)
      if (impersonation?.tenantId) {
        await endImpersonation(impersonation.tenantId);
      }
    } catch (error) {
      // Log error but don't block exit
      console.error('Failed to log impersonation end:', error);
    }
    
    // Clear impersonation state
    localStorage.removeItem('auth_token');
    localStorage.removeItem('impersonation_tenant');
    localStorage.removeItem('impersonation_tenant_id');
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
        disabled={exiting}
        className="text-amber-950 hover:text-amber-950 hover:bg-amber-600/30"
      >
        {exiting ? (
          <>
            <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            Exiting...
          </>
        ) : (
          <>
            <X className="h-4 w-4 mr-1" />
            Exit Impersonation
          </>
        )}
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
