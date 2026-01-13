import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  GitBranch,
  FileText,
  Users,
  Database,
  Package,
  PackageOpen,
  ClipboardList,
  ClipboardCheck,
  ChevronDown,
  ChevronRight,
  Settings,
  History,
  AlertTriangle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useState, useMemo } from 'react'
import { useAuthStore } from '@/stores/authStore'

interface NavItem {
  title: string
  href: string
  icon: React.ElementType
  /** If true, requires global admin access */
  adminOnly?: boolean
  /** If true, accessible by admin or study LEAD */
  adminOrLeadOnly?: boolean
}

interface NavGroup {
  title: string
  items: NavItem[]
}

const allNavigation: (NavItem | NavGroup)[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  {
    title: 'Data Management',
    items: [
      { title: 'Study Management', href: '/study-management', icon: GitBranch, adminOrLeadOnly: true },
      { title: 'TFL Properties', href: '/tfl-properties', icon: FileText, adminOrLeadOnly: true },
      { title: 'User Management', href: '/users', icon: Users, adminOnly: true },
      { title: 'Database Backup', href: '/database-backup', icon: Database, adminOnly: true },
      { title: 'Audit Logs', href: '/audit-logs', icon: History, adminOnly: true },
      { title: 'Error Logs', href: '/error-logs', icon: AlertTriangle, adminOnly: true },
      { title: 'Settings', href: '/settings', icon: Settings, adminOnly: true },
    ],
  },
  {
    title: 'Packages',
    items: [
      { title: 'Packages', href: '/packages', icon: Package, adminOrLeadOnly: true },
      { title: 'Package Items', href: '/package-items', icon: PackageOpen, adminOrLeadOnly: true },
    ],
  },
  {
    title: 'Reporting',
    items: [
      { title: 'Reporting Effort Items', href: '/reporting-effort-items', icon: ClipboardList, adminOrLeadOnly: true },
      { title: 'Tracker Management', href: '/tracker-management', icon: ClipboardCheck },
    ],
  },
]

function isNavGroup(item: NavItem | NavGroup): item is NavGroup {
  return 'items' in item
}

function NavItemLink({ item }: { item: NavItem }) {
  return (
    <NavLink
      to={item.href}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
          isActive
            ? 'bg-primary text-primary-foreground'
            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
        )
      }
    >
      <item.icon className="h-4 w-4" />
      {item.title}
    </NavLink>
  )
}

function NavGroupItem({ group, isAdmin, hasResponsibleAccess }: { group: NavGroup; isAdmin: boolean; hasResponsibleAccess: boolean }) {
  const location = useLocation()

  // Filter items based on permissions
  const visibleItems = useMemo(() => group.items.filter((item) => {
    if (item.adminOnly) return isAdmin
    if (item.adminOrLeadOnly) return isAdmin || hasResponsibleAccess
    return true
  }), [group.items, isAdmin, hasResponsibleAccess])
  
  // Check if any items are in the current path (for default open state)
  const hasActiveItem = visibleItems.some((item) => location.pathname === item.href)
  
  // useState must be called before any conditional returns
  const [isOpen, setIsOpen] = useState(hasActiveItem)

  // Don't render the group if no items are visible
  if (visibleItems.length === 0) return null

  return (
    <div className="space-y-1">
      <Button
        variant="ghost"
        className="w-full justify-between px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        onClick={() => setIsOpen(!isOpen)}
      >
        {group.title}
        {isOpen ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
      </Button>
      {isOpen && (
        <div className="ml-3 space-y-1 border-l pl-3">
          {visibleItems.map((item) => (
            <NavItemLink key={item.href} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}

export function Sidebar() {
  const { currentUser, hasResponsibleAccess, studyRolesLoading } = useAuthStore()
  const isAdmin = currentUser?.is_admin === true
  // If study roles are still loading, treat as no responsible access to prevent flash of unauthorized items
  const userHasResponsibleAccess = studyRolesLoading ? false : hasResponsibleAccess()
  
  // Filter navigation based on user permissions
  const navigation = useMemo(() => {
    return allNavigation.filter((item) => {
      if (isNavGroup(item)) {
        // Check if group has any visible items
        const visibleItems = item.items.filter((navItem) => {
          if (navItem.adminOnly) return isAdmin
          if (navItem.adminOrLeadOnly) return isAdmin || userHasResponsibleAccess
          return true
        })
        return visibleItems.length > 0
      } else {
        if (item.adminOnly) return isAdmin
        if (item.adminOrLeadOnly) return isAdmin || userHasResponsibleAccess
        return true
      }
    })
  }, [isAdmin, userHasResponsibleAccess])
  
  return (
    <aside className="hidden md:flex w-64 flex-col border-r bg-background">
      <ScrollArea className="flex-1 py-4">
        <nav className="space-y-2 px-3">
          {navigation.map((item, index) =>
            isNavGroup(item) ? (
              <NavGroupItem key={index} group={item} isAdmin={isAdmin} hasResponsibleAccess={userHasResponsibleAccess} />
            ) : (
              <NavItemLink key={item.href} item={item} />
            )
          )}
        </nav>
      </ScrollArea>
    </aside>
  )
}










