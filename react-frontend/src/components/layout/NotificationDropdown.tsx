import { useEffect } from 'react'
import { Bell, Check, CheckCheck, X, User, MessageSquare, UserPlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { useNotificationStore } from '@/stores/notificationStore'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/utils'
import type { NotificationData } from '@/api/endpoints/notifications'

function getNotificationIcon(type: string) {
  switch (type) {
    case 'assignment_prod':
      return <UserPlus className="h-4 w-4 text-blue-500" />
    case 'assignment_qc':
      return <User className="h-4 w-4 text-purple-500" />
    case 'comment_added':
      return <MessageSquare className="h-4 w-4 text-green-500" />
    default:
      return <Bell className="h-4 w-4" />
  }
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function NotificationItem({ 
  notification, 
  onAcknowledge 
}: { 
  notification: NotificationData
  onAcknowledge: (id: number) => void 
}) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 p-3 rounded-lg transition-colors",
        !notification.is_read 
          ? "bg-primary/5 border-l-2 border-primary" 
          : "bg-background hover:bg-accent"
      )}
    >
      <div className="flex-shrink-0 mt-1">
        {getNotificationIcon(notification.notification_type)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">
          {notification.title}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
          {notification.message}
        </p>
        <div className="flex items-center gap-2 mt-1">
          {notification.item_code && (
            <Badge variant="outline" className="text-[10px] px-1.5 py-0">
              {notification.item_code}
            </Badge>
          )}
          <span className="text-[10px] text-muted-foreground">
            {formatTimeAgo(notification.created_at)}
          </span>
        </div>
      </div>
      <Button
        variant="ghost"
        size="icon"
        className="h-6 w-6 flex-shrink-0 opacity-0 group-hover:opacity-100 hover:opacity-100"
        onClick={(e) => {
          e.stopPropagation()
          onAcknowledge(notification.id)
        }}
        title="Dismiss notification"
      >
        <X className="h-3 w-3" />
      </Button>
    </div>
  )
}

export function NotificationDropdown() {
  const { isAuthenticated } = useAuthStore()
  const {
    notifications,
    unreadCount,
    isLoading,
    isDropdownOpen,
    setDropdownOpen,
    fetchNotifications,
    fetchCount,
    acknowledge,
    acknowledgeAll,
  } = useNotificationStore()
  
  // Fetch notifications and count when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchCount()
    }
  }, [isAuthenticated, fetchCount])
  
  // Fetch full notifications when dropdown opens
  useEffect(() => {
    if (isDropdownOpen && isAuthenticated) {
      fetchNotifications()
    }
  }, [isDropdownOpen, isAuthenticated, fetchNotifications])
  
  if (!isAuthenticated) {
    return null
  }
  
  return (
    <DropdownMenu open={isDropdownOpen} onOpenChange={setDropdownOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
              <Badge 
                variant="destructive" 
                className="relative h-4 min-w-4 px-1 text-[10px] font-bold rounded-full flex items-center justify-center"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </Badge>
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Notifications</span>
          {notifications.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto py-0.5 px-2 text-xs"
              onClick={() => acknowledgeAll()}
            >
              <CheckCheck className="h-3 w-3 mr-1" />
              Clear all
            </Button>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        {isLoading ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            Loading notifications...
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-4 text-center">
            <Bell className="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
            <p className="text-sm text-muted-foreground">No new notifications</p>
            <p className="text-xs text-muted-foreground mt-1">
              You're all caught up!
            </p>
          </div>
        ) : (
          <ScrollArea className="h-[400px]">
            <div className="space-y-1 p-1">
              {notifications.map((notification) => (
                <div key={notification.id} className="group">
                  <NotificationItem
                    notification={notification}
                    onAcknowledge={acknowledge}
                  />
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
