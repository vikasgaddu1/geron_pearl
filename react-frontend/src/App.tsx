import { Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { Toaster } from 'sonner'
import { Loader2 } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { ProtectedRoute } from '@/features/auth/ProtectedRoute'
import { ImpersonationBanner } from '@/components/layout/ImpersonationBanner'

// Loading fallback component
function PageLoader() {
  return (
    <div className="flex h-[50vh] w-full items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  )
}

// Lazy load feature components for code splitting
const Dashboard = lazy(() => import('@/features/dashboard/Dashboard').then(m => ({ default: m.Dashboard })))
const StudyManagement = lazy(() => import('@/features/study-management/StudyManagement').then(m => ({ default: m.StudyManagement })))
const UserManagement = lazy(() => import('@/features/users/UserManagement').then(m => ({ default: m.UserManagement })))
const TFLProperties = lazy(() => import('@/features/tfl-properties/TFLProperties').then(m => ({ default: m.TFLProperties })))
const DatabaseBackup = lazy(() => import('@/features/database-backup/DatabaseBackup').then(m => ({ default: m.DatabaseBackup })))
const PackagesList = lazy(() => import('@/features/packages/PackagesList').then(m => ({ default: m.PackagesList })))
const PackageItems = lazy(() => import('@/features/packages/PackageItems').then(m => ({ default: m.PackageItems })))
const ReportingEffortItems = lazy(() => import('@/features/reporting/ReportingEffortItems').then(m => ({ default: m.ReportingEffortItems })))
const TrackerManagement = lazy(() => import('@/features/reporting/TrackerManagement').then(m => ({ default: m.TrackerManagement })))
const SettingsPage = lazy(() => import('@/features/settings/SettingsPage').then(m => ({ default: m.SettingsPage })))
const AuditLogsPage = lazy(() => import('@/features/audit-logs/AuditLogsPage').then(m => ({ default: m.AuditLogsPage })))
const ErrorLogsPage = lazy(() => import('@/features/error-logs/ErrorLogsPage').then(m => ({ default: m.ErrorLogsPage })))
const HelpPage = lazy(() => import('@/features/help').then(m => ({ default: m.HelpPage })))
const BillingPage = lazy(() => import('@/features/billing').then(m => ({ default: m.BillingPage })))

// Auth pages - lazy loaded
const LoginPage = lazy(() => import('@/features/auth/LoginPage').then(m => ({ default: m.LoginPage })))
const ForgotPasswordPage = lazy(() => import('@/features/auth/ForgotPasswordPage').then(m => ({ default: m.ForgotPasswordPage })))
const ResetPasswordPage = lazy(() => import('@/features/auth/ResetPasswordPage').then(m => ({ default: m.ResetPasswordPage })))

// Marketing pages - lazy loaded
const LandingPage = lazy(() => import('@/features/marketing').then(m => ({ default: m.LandingPage })))
const PricingPage = lazy(() => import('@/features/marketing').then(m => ({ default: m.PricingPage })))
const SignupPage = lazy(() => import('@/features/marketing').then(m => ({ default: m.SignupPage })))
const TermsPage = lazy(() => import('@/features/marketing').then(m => ({ default: m.TermsPage })))
const PrivacyPage = lazy(() => import('@/features/marketing').then(m => ({ default: m.PrivacyPage })))

// Super admin pages - lazy loaded (except protected route which must be synchronous)
import { SuperAdminProtectedRoute } from '@/features/super-admin'
const SuperAdminLoginPage = lazy(() => import('@/features/super-admin').then(m => ({ default: m.SuperAdminLoginPage })))
const SuperAdminDashboard = lazy(() => import('@/features/super-admin').then(m => ({ default: m.SuperAdminDashboard })))

function App() {
  return (
    <>
      <ImpersonationBanner />
      <Toaster position="top-right" richColors closeButton />
      <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* ============================================================
            PUBLIC MARKETING ROUTES (/)
            These are the public-facing pages for the SaaS marketing site
            ============================================================ */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        
        {/* ============================================================
            SUPER ADMIN ROUTES (/admin/*)
            Platform-level administration for super admins
            ============================================================ */}
        <Route path="/admin/login" element={<SuperAdminLoginPage />} />
        <Route 
          path="/admin/dashboard" 
          element={
            <SuperAdminProtectedRoute>
              <SuperAdminDashboard />
            </SuperAdminProtectedRoute>
          } 
        />
        <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />
        
        {/* Legacy route redirects - support old /login path */}
        <Route path="/login" element={<Navigate to="/app/login" replace />} />
        <Route path="/forgot-password" element={<Navigate to="/app/forgot-password" replace />} />
        <Route path="/reset-password/:token" element={<Navigate to="/app/reset-password/:token" replace />} />
        
        {/* ============================================================
            APP AUTH ROUTES (/app/login, etc.)
            These are authentication pages for the tenant application
            ============================================================ */}
        <Route path="/app/login" element={<LoginPage />} />
        <Route path="/app/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/app/reset-password/:token" element={<ResetPasswordPage />} />
        
        {/* ============================================================
            PROTECTED APP ROUTES (/app/*)
            These require authentication and are the main application
            ============================================================ */}
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/app/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          
          {/* Admin or Study Lead routes - accessible by global admins or users with LEAD role */}
          <Route
            path="study-management"
            element={
              <ProtectedRoute requireAdminOrLead>
                <StudyManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="tfl-properties"
            element={
              <ProtectedRoute requireAdminOrLead>
                <TFLProperties />
              </ProtectedRoute>
            }
          />
          <Route
            path="packages"
            element={
              <ProtectedRoute requireAdminOrLead>
                <PackagesList />
              </ProtectedRoute>
            }
          />
          <Route
            path="package-items"
            element={
              <ProtectedRoute requireAdminOrLead>
                <PackageItems />
              </ProtectedRoute>
            }
          />
          <Route
            path="reporting-effort-items"
            element={
              <ProtectedRoute requireAdminOrLead>
                <ReportingEffortItems />
              </ProtectedRoute>
            }
          />
          
          {/* Admin-only routes - accessible only by global admins */}
          <Route
            path="users"
            element={
              <ProtectedRoute requireAdmin>
                <UserManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="database-backup"
            element={
              <ProtectedRoute requireAdmin>
                <DatabaseBackup />
              </ProtectedRoute>
            }
          />
          <Route
            path="settings"
            element={
              <ProtectedRoute requireAdmin>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="audit-logs"
            element={
              <ProtectedRoute requireAdmin>
                <AuditLogsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="error-logs"
            element={
              <ProtectedRoute requireAdmin>
                <ErrorLogsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="billing"
            element={
              <ProtectedRoute requireAdmin>
                <BillingPage />
              </ProtectedRoute>
            }
          />

          {/* Help - accessible by all authenticated users */}
          <Route
            path="help"
            element={
              <ProtectedRoute>
                <HelpPage />
              </ProtectedRoute>
            }
          />

          {/* Accessible by all authenticated users - access based on study roles */}
          <Route
            path="tracker-management"
            element={
              <ProtectedRoute>
                <TrackerManagement />
              </ProtectedRoute>
            }
          />
        </Route>
        
        {/* ============================================================
            LEGACY ROUTE REDIRECTS
            Support old paths that didn't have /app prefix
            ============================================================ */}
        <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
        <Route path="/study-management" element={<Navigate to="/app/study-management" replace />} />
        <Route path="/users" element={<Navigate to="/app/users" replace />} />
        <Route path="/packages" element={<Navigate to="/app/packages" replace />} />
        <Route path="/tfl-properties" element={<Navigate to="/app/tfl-properties" replace />} />
        <Route path="/tracker-management" element={<Navigate to="/app/tracker-management" replace />} />
        <Route path="/settings" element={<Navigate to="/app/settings" replace />} />
        <Route path="/audit-logs" element={<Navigate to="/app/audit-logs" replace />} />
        <Route path="/help" element={<Navigate to="/app/help" replace />} />
      </Routes>
      </Suspense>
    </>
  )
}

export default App




