"""
Health check endpoints for monitoring and observability.

These endpoints are crucial for production deployment, load balancers,
and monitoring systems to verify service health.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
import structlog

from src.config.settings import Settings, get_settings_dependency
from src.models.chat_models import HealthCheckResponse
from src.services.ai_service import AzureOpenAIService


logger = structlog.get_logger()
router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    settings: Settings = Depends(get_settings_dependency)
) -> HealthCheckResponse:
    """
    Comprehensive health check endpoint.
    
    This endpoint checks:
    - Application basic functionality
    - Azure OpenAI connectivity
    - Database connectivity (when implemented)
    - Overall system health
    
    Used by:
    - Load balancers for routing decisions
    - Monitoring systems for alerting
    - Container orchestrators for restart decisions
    """
    try:
        # Test Azure OpenAI connectivity
        azure_openai_status = "disconnected"
        try:
            async with AzureOpenAIService(settings) as ai_service:
                if await ai_service.health_check():
                    azure_openai_status = "connected"
                else:
                    azure_openai_status = "error"
        except Exception as e:
            logger.warning("Azure OpenAI health check failed", error=str(e))
            azure_openai_status = "error"
        
        # Database status (placeholder - implement when database is added)
        database_status = "connected"  # Will be actual check later
        
        # Determine overall status
        if azure_openai_status == "connected" and database_status == "connected":
            overall_status = "healthy"
        elif azure_openai_status in ["connected", "disconnected"]:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            azure_openai_status=azure_openai_status,
            database_status=database_status,
            response_time_ms=None,  # Could track average response time
            active_conversations=None  # Could track active sessions
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )


@router.get("/health/live")
async def liveness_probe() -> Dict[str, Any]:
    """
    Kubernetes liveness probe endpoint.
    
    Simple check that the application is running and can respond.
    Kubernetes uses this to determine if it should restart the pod.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready")
async def readiness_probe(
    settings: Settings = Depends(get_settings_dependency)
) -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    
    Checks if the application is ready to serve traffic.
    Kubernetes uses this to determine if it should route traffic to the pod.
    """
    try:
        # Quick check of critical dependencies
        async with AzureOpenAIService(settings) as ai_service:
            ready = await ai_service.health_check()
        
        if ready:
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=503,
                detail="Service not ready - dependencies unavailable"
            )
            
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Service not ready"
        )