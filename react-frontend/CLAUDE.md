# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the PEARL React frontend.

## Essential Commands

```bash
npm run dev       # Start development server (port 5173)
npm run build     # Build for production with TypeScript check
npm run lint      # ESLint
npm run preview   # Preview production build locally
```

## Project Structure

```
src/
├── api/                    # API layer
│   ├── client.ts           # Axios instance with interceptors
│   ├── endpoints/          # Typed API functions per entity
│   └── index.ts            # Consolidated exports
├── components/             # Reusable components
│   ├── ui/                 # shadcn/ui primitives (Button, Dialog, etc.)
│   ├── layout/             # Layout components (Navbar, Sidebar, NotificationDropdown)
│   └── common/             # Shared components (DataTable, filters)
├── features/               # Feature modules
│   ├── dashboard/          # Programmer and Tracker dashboards
│   ├── study-management/   # Study tree hierarchy
│   ├── packages/           # Package and PackageItem management
│   ├── reporting/          # ReportingEffort, Items, Tracker
│   ├── users/              # User management
│   ├── tfl-properties/     # TextElement management
│   └── database-backup/    # Backup operations
├── hooks/                  # Custom React hooks
├── stores/                 # Zustand stores for global state
├── types/                  # TypeScript type definitions
├── lib/                    # Utilities (cn, formatters)
├── App.tsx                 # Root component with routing
└── main.tsx                # Entry point
```

## Key Patterns

### API Calls
All API functions are in `src/api/endpoints/`. Use TanStack Query for data fetching:

```typescript
// In components
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { studiesApi } from '@/api';

const { data, isLoading } = useQuery({
  queryKey: ['studies'],
  queryFn: studiesApi.getAll
});
```

### Form Handling
Use React Hook Form with Zod validation:

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1, 'Required'),
  email: z.string().email()
});

const form = useForm({
  resolver: zodResolver(schema)
});
```

### State Management
- **Server state**: TanStack Query (caching, refetching, mutations)
- **Global client state**: Zustand stores in `src/stores/` (authStore, notificationStore)
- **Local component state**: `useState`/`useReducer`

### WebSocket Integration
WebSocket manager handles real-time updates. Events trigger TanStack Query cache invalidation:

```typescript
// WebSocket events invalidate queries
queryClient.invalidateQueries({ queryKey: ['studies'] });
```

### Notification System

The `NotificationDropdown` component (in `components/layout/`) shows user notifications with real-time updates:

```typescript
import { useNotificationStore } from '@/stores/notificationStore';

const { 
  notifications,      // List of notifications
  unreadCount,        // Badge count
  fetchNotifications, // Fetch full list
  acknowledge,        // Dismiss single notification
  acknowledgeAll      // Clear all
} = useNotificationStore();
```

**Notification Types:**
| Type | Icon | Description |
|------|------|-------------|
| `assignment_prod` | UserPlus (blue) | Assigned as production programmer |
| `assignment_qc` | User (purple) | Assigned as QC programmer |
| `comment_added` | MessageSquare (green) | New comment on assigned item |

WebSocket events `notification_created` and `notification_count_updated` automatically update the notification badge.

### Role-Based UI

Use auth store helpers to conditionally render UI based on user roles:

```typescript
import { useAuthStore } from '@/stores/authStore';

const { currentUser, isLeadForStudy, hasLeadAccess } = useAuthStore();

// Check if user is global admin
const isAdmin = currentUser?.is_admin;

// Check if user is LEAD for a specific study (or admin)
const canEditStudy = isAdmin || isLeadForStudy(studyId);

// Check if user has LEAD access in any study (for global resources like packages)
const canManagePackages = isAdmin || hasLeadAccess();
```

For protected routes in `App.tsx`:

```typescript
<ProtectedRoute requireAdminOrLead>  {/* Admin or any LEAD */}
<ProtectedRoute requireAdmin>        {/* Admin only */}
```

**Permission matrix:**
| Resource | Admin | LEAD (own study) | LEAD (other study) | EDITOR/VIEWER |
|----------|-------|------------------|--------------------|--------------| 
| Study Management (own studies) | ✅ | ✅ | ❌ | ❌ |
| Packages & TFL Properties | ✅ | ✅ | ✅ | ❌ |
| User Management | ✅ | ❌ | ❌ | ❌ |
| Settings & Backup | ✅ | ❌ | ❌ | ❌ |
| Director Dashboard | ✅ | ❌ | ❌ | ❌ |

### shadcn/ui Components
Import from `@/components/ui/`:

```typescript
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
```

## TFL Properties (Text Elements)

The TFL Properties feature manages reusable text components for TLF outputs. The backend stores two fields (`label` and `content`) but their semantic meaning varies by type:

| Type | `label` Field Meaning | `content` Field Meaning |
|------|----------------------|------------------------|
| **Titles** | Category (Safety, Efficacy, General) | The actual title text |
| **Footnotes** | Category (Safety, Efficacy, General) | The actual footnote text |
| **Population Sets** | Short Form / ADaM Variable (SAFFL, ITTFL) | Full Name (Safety Population) |
| **Acronyms** | Abbreviation (AE, SAE, SD) | Full Form (Adverse Event) |
| **ICH Categories** | ICH Code (ICH_11.4, ICH_12.2) | Full Description |

The UI dynamically displays context-appropriate labels using `TYPE_FIELD_LABELS` configuration in `TFLProperties.tsx`. When adding or viewing:
- **Titles tab**: Shows "Category" and "Title Text" columns
- **Acronyms tab**: Shows "Abbreviation" and "Full Form" columns
- **Population Sets tab**: Shows "Short Form" and "Full Name" columns

This pattern keeps the backend schema simple while providing intuitive, domain-specific terminology in the UI.

## Environment Variables

Prefix with `VITE_`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/v1/ws/studies
```

## Data Tables

Use TanStack Table for complex tables with filtering:

```typescript
import { useReactTable, getCoreRowModel, getFilteredRowModel } from '@tanstack/react-table';

const table = useReactTable({
  data,
  columns,
  getCoreRowModel: getCoreRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
});
```

## Adding a New Feature

1. Create types in `src/types/`
2. Add API endpoints in `src/api/endpoints/`
3. Create feature folder in `src/features/`
4. Add route in `App.tsx`
5. Create navigation link if needed

## Common Issues

| Issue | Solution |
|-------|----------|
| Type errors on build | Run `npm run build` to see full errors |
| Query not refetching | Check `queryKey` matches and `invalidateQueries` call |
| Component not re-rendering | Verify dependency arrays and state updates |
| WebSocket not syncing | Check browser console for connection errors |
| Styles not applying | Ensure Tailwind classes are valid; check `tailwind.config.js` |

## Import Aliases

Use `@/` alias for clean imports:

```typescript
import { Button } from '@/components/ui/button';
import { studiesApi } from '@/api';
import { useAuthStore } from '@/stores/auth';
```
