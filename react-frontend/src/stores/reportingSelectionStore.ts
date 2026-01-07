import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ReportingSelectionState {
  selectedStudyId: string
  selectedReleaseId: string
  selectedEffortId: string
  setSelectedStudyId: (id: string) => void
  setSelectedReleaseId: (id: string) => void
  setSelectedEffortId: (id: string) => void
  clearSelection: () => void
}

export const useReportingSelectionStore = create<ReportingSelectionState>()(
  persist(
    (set) => ({
      selectedStudyId: '',
      selectedReleaseId: '',
      selectedEffortId: '',
      setSelectedStudyId: (id) => set({ selectedStudyId: id, selectedReleaseId: '', selectedEffortId: '' }),
      setSelectedReleaseId: (id) => set({ selectedReleaseId: id, selectedEffortId: '' }),
      setSelectedEffortId: (id) => set({ selectedEffortId: id }),
      clearSelection: () => set({ selectedStudyId: '', selectedReleaseId: '', selectedEffortId: '' }),
    }),
    {
      name: 'pearl-reporting-selection',
    }
  )
)





