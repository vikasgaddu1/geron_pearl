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
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useState } from 'react'

interface NavItem {
  title: string
  href: string
  icon: React.ElementType
}

interface NavGroup {
  title: string
  items: NavItem[]
}

const navigation: (NavItem | NavGroup)[] = [
  { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  {
    title: 'Data Management',
    items: [
      { title: 'Study Management', href: '/study-management', icon: GitBranch },
      { title: 'TFL Properties', href: '/tfl-properties', icon: FileText },
      { title: 'User Management', href: '/users', icon: Users },
      { title: 'Database Backup', href: '/database-backup', icon: Database },
    ],
  },
  {
    title: 'Packages',
    items: [
      { title: 'Packages', href: '/packages', icon: Package },
      { title: 'Package Items', href: '/package-items', icon: PackageOpen },
    ],
  },
  {
    title: 'Reporting',
    items: [
      { title: 'Reporting Effort Items', href: '/reporting-effort-items', icon: ClipboardList },
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

function NavGroupItem({ group }: { group: NavGroup }) {
  const location = useLocation()
  const [isOpen, setIsOpen] = useState(
    group.items.some((item) => location.pathname === item.href)
  )

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
          {group.items.map((item) => (
            <NavItemLink key={item.href} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}

export function Sidebar() {
  return (
    <aside className="hidden md:flex w-64 flex-col border-r bg-background">
      <ScrollArea className="flex-1 py-4">
        <nav className="space-y-2 px-3">
          {navigation.map((item, index) =>
            isNavGroup(item) ? (
              <NavGroupItem key={index} group={item} />
            ) : (
              <NavItemLink key={item.href} item={item} />
            )
          )}
        </nav>
      </ScrollArea>
    </aside>
  )
}

