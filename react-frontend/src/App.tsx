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

function App() {
  return (
    <>
      <Toaster position="top-right" richColors closeButton />
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
        
        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
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
      </Routes>
    </>
  )
}

export default App




