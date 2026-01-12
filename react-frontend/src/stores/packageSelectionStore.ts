import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface PackageSelectionState {
  selectedPackageId: string
  setSelectedPackageId: (id: string) => void
  clearSelection: () => void
}

export const usePackageSelectionStore = create<PackageSelectionState>()(
  persist(
    (set) => ({
      selectedPackageId: '',
      setSelectedPackageId: (id) => set({ selectedPackageId: id }),
      clearSelection: () => set({ selectedPackageId: '' }),
    }),
    {
      name: 'pearl-package-selection',
    }
  )
)
