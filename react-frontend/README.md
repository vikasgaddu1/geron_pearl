# PEARL Admin Frontend (React)

Modern React-based admin frontend for the PEARL Research Data Management System.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and optimized builds
- **Tailwind CSS** with shadcn/ui components
- **TanStack Query** for data fetching and caching
- **TanStack Table** for powerful data tables
- **React Router** for client-side routing
- **Zustand** for state management
- **Recharts** for data visualization
- **React Hook Form + Zod** for form handling

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or pnpm
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/v1/ws/studies
```

## Project Structure

```
src/
├── api/                    # API client and endpoints
│   ├── client.ts           # Axios instance
│   ├── endpoints/          # API endpoint functions
│   └── index.ts            # Exports
├── components/             # Reusable components
│   ├── ui/                 # shadcn/ui primitives
│   ├── layout/             # Layout components
│   └── common/             # Shared components
├── features/               # Feature modules
│   ├── dashboard/          # Dashboard views
│   ├── study-management/   # Study tree
│   ├── packages/           # Package management
│   ├── reporting/          # Tracker and items
│   ├── users/              # User management
│   ├── tfl-properties/     # Text elements
│   └── database-backup/    # Backup management
├── hooks/                  # Custom React hooks
├── lib/                    # Utilities
├── stores/                 # Zustand stores
├── types/                  # TypeScript types
├── App.tsx                 # Main app component
└── main.tsx                # Entry point
```

## Features

- **Dashboard**: Programmer and Tracker dashboards with metrics and charts
- **Study Management**: Hierarchical tree view for studies, releases, and efforts
- **Package Management**: Template packages with TLF and Dataset items
- **Tracker Management**: Assignment tracking with bulk operations
- **User Management**: CRUD for system users with role assignments
- **TFL Properties**: Manage titles, footnotes, populations, and acronyms
- **Database Backup**: Create, list, restore, and delete backups
- **Real-time Updates**: WebSocket integration for live data sync
- **Dark Mode**: System-aware theme with manual toggle

## Development

### Code Quality

```bash
# Lint code
npm run lint
```

### Building

```bash
# Type check and build
npm run build
```

## API Integration

The frontend connects to the FastAPI backend. All API endpoints are defined in `src/api/endpoints/` with full TypeScript types.

### WebSocket

Real-time updates are handled through WebSocket connection to `/api/v1/ws/studies`. The WebSocket manager automatically reconnects on disconnection.

## Developer Documentation

For detailed technical documentation, see the [`docs/`](./docs/) folder:

- **[Filtering Implementation Guide](./docs/FILTERING_IMPLEMENTATION_GUIDE.md)** - Advanced table filtering with wildcards, regex, and multi-select
- **[Implementation Status](./docs/IMPLEMENTATION_STATUS.md)** - Feature implementation status and testing checklist
- **[Migration Complete](./docs/MIGRATION_COMPLETE.md)** - R Shiny to React migration summary and achievements

## Contributing

1. Follow the existing code patterns
2. Use TypeScript strictly
3. Add proper error handling
4. Test UI changes across light/dark modes


