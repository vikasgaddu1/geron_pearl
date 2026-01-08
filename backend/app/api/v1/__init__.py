"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    auth, studies, database_releases, reporting_efforts, websocket, text_elements, packages, users,
    reporting_effort_items, reporting_effort_tracker, tracker_comments, tracker_tags,
    audit_trail, database_backup, settings, reporting_effort_milestones, ig_versions,
    reporting_effort_usecases, team_assignments, analytics
)

api_router = APIRouter()

# Include auth router (no auth required for these endpoints)
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include all endpoint routers
api_router.include_router(studies.router, prefix="/studies", tags=["studies"])
api_router.include_router(database_releases.router, prefix="/database-releases", tags=["database-releases"])
api_router.include_router(reporting_efforts.router, prefix="/reporting-efforts", tags=["reporting-efforts"])
api_router.include_router(text_elements.router, prefix="/text-elements", tags=["text-elements"])
api_router.include_router(packages.router, prefix="/packages", tags=["packages"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Reporting Effort Tracker System endpoints
api_router.include_router(reporting_effort_items.router, prefix="/reporting-effort-items", tags=["reporting-effort-items"])
api_router.include_router(reporting_effort_tracker.router, prefix="/reporting-effort-tracker", tags=["reporting-effort-tracker"])
api_router.include_router(tracker_comments.router, prefix="/tracker-comments", tags=["tracker-comments"])
api_router.include_router(tracker_tags.router, prefix="/tracker-tags", tags=["tracker-tags"])

# Admin endpoints
api_router.include_router(audit_trail.router, prefix="/audit-trail", tags=["audit-trail"])
api_router.include_router(database_backup.router, prefix="/database-backup", tags=["database-backup"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(ig_versions.router, prefix="/ig-versions", tags=["ig-versions"])

# Milestone tracking
api_router.include_router(reporting_effort_milestones.router, prefix="/milestones", tags=["milestones"])

# Use case management
api_router.include_router(reporting_effort_usecases.router, prefix="/use-cases", tags=["use-cases"])

# Team allocation and capacity planning
api_router.include_router(team_assignments.router, prefix="/team-assignments", tags=["team-assignments"])

# Analytics and Director Dashboard
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])