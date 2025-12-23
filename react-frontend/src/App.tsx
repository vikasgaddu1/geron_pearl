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
          
          {/* Admin-only routes */}
          <Route
            path="study-management"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <StudyManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="tfl-properties"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <TFLProperties />
              </ProtectedRoute>
            }
          />
          <Route
            path="users"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <UserManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="database-backup"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <DatabaseBackup />
              </ProtectedRoute>
            }
          />
          <Route
            path="packages"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <PackagesList />
              </ProtectedRoute>
            }
          />
          <Route
            path="package-items"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <PackageItems />
              </ProtectedRoute>
            }
          />
          <Route
            path="reporting-effort-items"
            element={
              <ProtectedRoute requiredRole="ADMIN">
                <ReportingEffortItems />
              </ProtectedRoute>
            }
          />
          
          {/* Accessible by EDITOR+ */}
          <Route
            path="tracker-management"
            element={
              <ProtectedRoute requiredRole="EDITOR">
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

