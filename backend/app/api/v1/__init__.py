"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import studies, database_releases, reporting_efforts, websocket, text_elements, acronyms, acronym_sets, acronym_set_members

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(studies.router, prefix="/studies", tags=["studies"])
api_router.include_router(database_releases.router, prefix="/database-releases", tags=["database-releases"])
api_router.include_router(reporting_efforts.router, prefix="/reporting-efforts", tags=["reporting-efforts"])
api_router.include_router(text_elements.router, prefix="/text-elements", tags=["text-elements"])
api_router.include_router(acronyms.router, prefix="/acronyms", tags=["acronyms"])
api_router.include_router(acronym_sets.router, prefix="/acronym-sets", tags=["acronym-sets"])
api_router.include_router(acronym_set_members.router, prefix="/acronym-set-members", tags=["acronym-set-members"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])