"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import studies, database_releases, websocket

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(studies.router, prefix="/studies", tags=["studies"])
api_router.include_router(database_releases.router, prefix="/database-releases", tags=["database-releases"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])