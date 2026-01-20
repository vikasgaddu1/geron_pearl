import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AppShell } from '@/components/layout/AppShell'
import { Dashboard } from '@/features/dashboard/Dashboard'
import { StudyManagement } from '@/features/study-management/StudyManagement'
import { UserManagement } from '@/features/users/UserManagement'
import { TFLProperties } from '@/features/tfl-properties/TFLProperties'
import { DatabaseBackup } from '@/features/database-backup/DatabaseBackup'
import { PackagesList } from '@/features/packages/PackagesList'
import { PackageItems } from '@/features/packages/PackageItems'
import { ReportingEffortItems } from '@/features/reporting/ReportingEffortItems'
import { TrackerManagement } from '@/features/reporting/TrackerManagement'
import { LoginPage } from '@/features/auth/LoginPage'
import { ForgotPasswordPage } from '@/features/auth/ForgotPasswordPage'
import { ResetPasswordPage } from '@/features/auth/ResetPasswordPage'
import { ProtectedRoute } from '@/features/auth/ProtectedRoute'
import { SettingsPage } from '@/features/settings/SettingsPage'
import { AuditLogsPage } from '@/features/audit-logs/AuditLogsPage'
import { ErrorLogsPage } from '@/features/error-logs/ErrorLogsPage'
import { LandingPage, PricingPage, SignupPage, TermsPage, PrivacyPage } from '@/features/marketing'

function App() {
  return (
    <>
      <Toaster position="top-right" richColors closeButton />
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
      </Routes>
    </>
  )
}

export default App




