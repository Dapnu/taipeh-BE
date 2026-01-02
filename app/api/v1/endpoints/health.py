"""
Health check endpoint
"""

from fastapi import APIRouter, status
from datetime import datetime
from app.core.database import SupabaseClient
from app.core.config import settings

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the API and database connection"
)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        dict: Health status information including API status, database status, and timestamp
    """
    # Check database connection
    db_healthy = await SupabaseClient.health_check()
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "api": {
            "status": "operational",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        },
        "database": {
            "status": "connected" if db_healthy else "disconnected",
            "type": "supabase"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
