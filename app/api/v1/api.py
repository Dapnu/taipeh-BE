"""
API v1 router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, models, predictions, routes

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(models.router, tags=["models"])
api_router.include_router(predictions.router, tags=["predictions"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
