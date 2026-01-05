import { Palette, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useUIStore, applyColorTheme, COLOR_THEMES } from '@/stores/uiStore'
import { useEffect } from 'react'
import { cn } from '@/lib/utils'

export function ThemeSelector() {
  const { colorTheme, setColorTheme } = useUIStore()

  useEffect(() => {
    applyColorTheme(colorTheme)
  }, [colorTheme])

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <Palette className="h-5 w-5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel>Color Theme</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {COLOR_THEMES.map((theme) => (
          <DropdownMenuItem
            key={theme.value}
            onClick={() => setColorTheme(theme.value)}
            className="flex items-center gap-3 cursor-pointer"
          >
            <span
              className="h-4 w-4 rounded-full border border-border"
              style={{ backgroundColor: theme.color }}
            />
            <span className="flex-1">{theme.label}</span>
            {colorTheme === theme.value && (
              <Check className={cn("h-4 w-4")} />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
