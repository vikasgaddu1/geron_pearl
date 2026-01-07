import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'
type ColorTheme = 'default' | 'teal' | 'emerald' | 'coral' | 'slate' | 'indigo'

export const COLOR_THEMES: { value: ColorTheme; label: string; color: string }[] = [
  { value: 'default', label: 'Blue', color: 'hsl(221.2, 83.2%, 53.3%)' },
  { value: 'teal', label: 'Teal', color: 'hsl(175, 84%, 32%)' },
  { value: 'emerald', label: 'Emerald', color: 'hsl(152, 69%, 31%)' },
  { value: 'coral', label: 'Coral', color: 'hsl(16, 85%, 57%)' },
  { value: 'slate', label: 'Slate', color: 'hsl(215, 25%, 35%)' },
  { value: 'indigo', label: 'Indigo', color: 'hsl(243, 75%, 59%)' },
]

interface UIState {
  theme: Theme
  colorTheme: ColorTheme
  sidebarCollapsed: boolean
  setTheme: (theme: Theme) => void
  setColorTheme: (colorTheme: ColorTheme) => void
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'system',
      colorTheme: 'default',
      sidebarCollapsed: false,
      setTheme: (theme) => set({ theme }),
      setColorTheme: (colorTheme) => set({ colorTheme }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
    }),
    {
      name: 'pearl-ui-storage',
    }
  )
)

// Helper to apply theme (light/dark mode)
export function applyTheme(theme: Theme) {
  const root = window.document.documentElement
  root.classList.remove('light', 'dark')

  if (theme === 'system') {
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light'
    root.classList.add(systemTheme)
  } else {
    root.classList.add(theme)
  }
}

// Helper to apply color theme
export function applyColorTheme(colorTheme: ColorTheme) {
  const root = window.document.documentElement
  // Remove all color theme classes
  COLOR_THEMES.forEach((t) => {
    if (t.value !== 'default') {
      root.classList.remove(`theme-${t.value}`)
    }
  })
  // Add new color theme class (unless default)
  if (colorTheme !== 'default') {
    root.classList.add(`theme-${colorTheme}`)
  }
}








