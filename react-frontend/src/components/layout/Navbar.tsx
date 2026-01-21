import { Link } from 'react-router-dom'
import { Moon, Sun, Menu, LogOut, User, Gem, Wifi, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { useUIStore, applyTheme } from '@/stores/uiStore'
import { useWebSocketStore } from '@/stores/websocketStore'
import { useAuthStore } from '@/stores/authStore'
import { useAuth } from '@/hooks/useAuth'
import { Badge } from '@/components/ui/badge'
import { ThemeSelector } from '@/components/layout/ThemeSelector'
import { NotificationDropdown } from '@/components/layout/NotificationDropdown'
import { useEffect } from 'react'

export function Navbar() {
  const { theme, setTheme, toggleSidebar } = useUIStore()
  const wsStatus = useWebSocketStore((state) => state.status)
  const currentUser = useAuthStore((state) => state.currentUser)
  const { logout } = useAuth()

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
  }

  const handleLogout = async () => {
    await logout()
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4 gap-4">
        <Button variant="ghost" size="icon" className="md:hidden" onClick={toggleSidebar} aria-label="Toggle navigation menu">
          <Menu className="h-5 w-5" />
        </Button>

        <Tooltip>
          <TooltipTrigger asChild>
            <Link to="/app/dashboard" className="flex items-center gap-2 font-semibold group">
              <Gem className="h-6 w-6 text-primary group-hover:scale-110 transition-transform" />
              <div className="hidden sm:flex flex-col leading-none">
                <span className="text-lg font-bold tracking-tight gradient-primary-text">
                  PEARL
                </span>
                <span className="text-[10px] text-muted-foreground font-normal tracking-wide">
                  Clinical Research Management
                </span>
              </div>
            </Link>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="max-w-xs">
            <p className="font-semibold">Package, Effort, and Analysis Reporting Library</p>
            <p className="text-xs text-muted-foreground mt-1">
              Comprehensive clinical research data management system
            </p>
          </TooltipContent>
        </Tooltip>

        <div className="flex-1" />

        <div className="flex items-center gap-2">
          {/* Color Theme Selector */}
          <ThemeSelector />

          {/* Light/Dark Mode Toggle */}
          <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
            {theme === 'dark' ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>

          {/* WebSocket Status Indicator */}
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center">
                {wsStatus === 'connected' ? (
                  <Wifi className="h-4 w-4 text-green-500" />
                ) : (
                  <WifiOff className="h-4 w-4 text-red-500" />
                )}
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>Real-time sync: {wsStatus}</p>
            </TooltipContent>
          </Tooltip>

          {/* Notifications */}
          <NotificationDropdown />

          {/* User Dropdown */}
          {currentUser && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  <span className="hidden sm:inline-block font-medium">{currentUser.username}</span>
                  <Badge variant="outline" className={currentUser.is_admin 
                    ? 'bg-primary/10 text-primary border-primary/20' 
                    : 'bg-muted text-muted-foreground'}>
                    {currentUser.is_admin ? 'Admin' : 'User'}
                  </Badge>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <span className="font-semibold">{currentUser.username}</span>
                    {currentUser.email && (
                      <span className="text-xs text-muted-foreground">{currentUser.email}</span>
                    )}
                    <div className="pt-1">
                      <Badge variant="outline" className={currentUser.is_admin 
                        ? 'bg-primary/10 text-primary border-primary/20' 
                        : 'bg-muted text-muted-foreground'}>
                        {currentUser.is_admin ? 'Global Admin' : 'User'}
                      </Badge>
                    </div>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600 focus:text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Logout</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </header>
  )
}


