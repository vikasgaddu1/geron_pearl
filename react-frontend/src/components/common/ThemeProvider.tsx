import { useEffect } from 'react'
import { useUIStore, applyTheme } from '@/stores/uiStore'
import { usePrefersDarkMode } from '@/hooks/useMediaQuery'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme } = useUIStore()
  const prefersDark = usePrefersDarkMode()

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  useEffect(() => {
    if (theme === 'system') {
      const root = window.document.documentElement
      root.classList.remove('light', 'dark')
      root.classList.add(prefersDark ? 'dark' : 'light')
    }
  }, [theme, prefersDark])

  return <>{children}</>
}

