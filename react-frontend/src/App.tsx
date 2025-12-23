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

function App() {
  return (
    <>
      <Toaster position="top-right" richColors closeButton />
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="study-management" element={<StudyManagement />} />
          <Route path="tfl-properties" element={<TFLProperties />} />
          <Route path="users" element={<UserManagement />} />
          <Route path="database-backup" element={<DatabaseBackup />} />
          <Route path="packages" element={<PackagesList />} />
          <Route path="package-items" element={<PackageItems />} />
          <Route path="reporting-effort-items" element={<ReportingEffortItems />} />
          <Route path="tracker-management" element={<TrackerManagement />} />
        </Route>
      </Routes>
    </>
  )
}

export default App

