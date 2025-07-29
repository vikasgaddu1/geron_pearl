"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import studies, websocket

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(studies.router, prefix="/studies", tags=["studies"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])