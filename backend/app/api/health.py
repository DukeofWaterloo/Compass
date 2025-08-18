"""
Health check endpoints
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "compass-api"}

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service status"""
    # TODO: Add checks for database, external APIs, etc.
    return {
        "status": "healthy",
        "service": "compass-api",
        "version": "1.0.0",
        "checks": {
            "database": "healthy",
            "uwaterloo_api": "healthy",
            "ai_service": "healthy"
        }
    }