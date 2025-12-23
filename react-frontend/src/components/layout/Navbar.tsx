import { Link } from 'react-router-dom'
import { Database, Bell, Moon, Sun, Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useUIStore, applyTheme } from '@/stores/uiStore'
import { useWebSocketStore } from '@/stores/websocketStore'
import { cn } from '@/lib/utils'
import { useEffect } from 'react'

export function Navbar() {
  const { theme, setTheme, toggleSidebar } = useUIStore()
  const wsStatus = useWebSocketStore((state) => state.status)

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4 gap-4">
        <Button variant="ghost" size="icon" className="md:hidden" onClick={toggleSidebar}>
          <Menu className="h-5 w-5" />
        </Button>

        <Link to="/" className="flex items-center gap-2 font-semibold">
          <Database className="h-6 w-6 text-primary" />
          <span className="hidden sm:inline-block bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
            PEARL Admin
          </span>
        </Link>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          {/* Theme Toggle */}
          <Button variant="ghost" size="icon" onClick={toggleTheme}>
            {theme === 'dark' ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>

          {/* Status Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-5 w-5" />
                <span
                  className={cn(
                    "absolute top-1 right-1 h-2 w-2 rounded-full",
                    wsStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
                  )}
                />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>System Status</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="flex items-center gap-2">
                <span
                  className={cn(
                    "h-2 w-2 rounded-full",
                    wsStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
                  )}
                />
                <span>WebSocket: {wsStatus}</span>
              </DropdownMenuItem>
              <DropdownMenuItem className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                <span>API: Connected</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <span className="text-xs text-muted-foreground">
                  Last checked: {new Date().toLocaleTimeString()}
                </span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}

