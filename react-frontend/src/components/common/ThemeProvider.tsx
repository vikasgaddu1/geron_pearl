import { useEffect } from 'react'
import { useUIStore, applyTheme, applyColorTheme } from '@/stores/uiStore'
import { usePrefersDarkMode } from '@/hooks/useMediaQuery'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme, colorTheme } = useUIStore()
  const prefersDark = usePrefersDarkMode()

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  useEffect(() => {
    applyColorTheme(colorTheme)
  }, [colorTheme])

  useEffect(() => {
    if (theme === 'system') {
      const root = window.document.documentElement
      root.classList.remove('light', 'dark')
      root.classList.add(prefersDark ? 'dark' : 'light')
    }
  }, [theme, prefersDark])

  return <>{children}</>
}




