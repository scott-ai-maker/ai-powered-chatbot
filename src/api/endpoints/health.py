"""
Health check endpoints for monitoring and observability.

These endpoints are crucial for production deployment, load balancers,
and monitoring systems to verify service health.
"""

from datetime import datetime
from typing import Dict, Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException
import structlog

from src.config.settings import Settings, get_settings_dependency
from src.models.chat_models import HealthCheckResponse
from src.services.ai_service import AzureOpenAIService
from src.services.monitoring_service import get_monitoring_service


logger = structlog.get_logger()
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint for Azure Container Apps.

    Returns HTTP 200 if the service is running and can handle requests.
    This endpoint is used by:
    - Azure Container Apps health probes
    - Load balancers
    - Monitoring systems
    - Docker health checks
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "AI Career Mentor Chatbot",
        "version": "1.0.0",
    }


@router.get("/health/ready")
async def readiness_check(
    settings: Settings = Depends(get_settings_dependency),
) -> Dict[str, Any]:
    """
    Readiness check endpoint for Azure Container Apps.

    Returns HTTP 200 if the service is ready to handle requests.
    Checks that all required dependencies are configured.
    """
    try:
        # Check critical configuration
        checks = {
            "config_loaded": True,
            "azure_openai_configured": bool(
                settings.azure_openai_endpoint and settings.azure_openai_key
            ),
            "azure_search_configured": bool(
                settings.azure_search_endpoint and settings.azure_search_key
            ),
            "cosmos_db_configured": bool(
                settings.azure_cosmos_endpoint and settings.azure_cosmos_key
            ),
        }

        # Determine overall readiness
        all_ready = all(checks.values())

        response = {
            "status": "ready" if all_ready else "not_ready",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": "AI Career Mentor Chatbot",
            "checks": checks,
        }

        if not all_ready:
            logger.warning("Service not ready", checks=checks)
            return response

        return response

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/health/detailed", response_model=HealthCheckResponse)
async def detailed_health_check(
    settings: Settings = Depends(get_settings_dependency),
) -> HealthCheckResponse:
    """
    Comprehensive health check endpoint with full diagnostics.

    This endpoint checks:
    - Application basic functionality
    - Azure OpenAI connectivity
    - Database connectivity (when implemented)
    - Monitoring system health
    - Overall system health

    Used by:
    - Monitoring dashboards
    - Debugging and diagnostics
    - Administrative oversight
    """
    monitoring = get_monitoring_service(settings)

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

        # Get monitoring health metrics
        monitoring_metrics = await monitoring.get_health_metrics()

        # Determine overall status
        if azure_openai_status == "connected" and database_status == "connected":
            overall_status = "healthy"
        elif azure_openai_status in ["connected", "disconnected"]:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return HealthCheckResponse(
            status=cast(Literal["healthy", "degraded", "unhealthy"], overall_status),
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            azure_openai_status=cast(
                Literal["connected", "disconnected", "error"], azure_openai_status
            ),
            database_status=cast(
                Literal["connected", "disconnected", "error"], database_status
            ),
            response_time_ms=int(monitoring_metrics.get("uptime_seconds", 0) * 1000),
            active_conversations=int(monitoring_metrics.get("metrics_summary", {})
            .get("sample_metrics", {})
            .get("chat_requests", 0)),
        )

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


@router.get("/health/live")
async def liveness_probe() -> Dict[str, Any]:
    """
    Kubernetes liveness probe endpoint.

    Simple check that the application is running and can respond.
    Kubernetes uses this to determine if it should restart the pod.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/metrics")
async def metrics_endpoint(
    settings: Settings = Depends(get_settings_dependency),
) -> Dict[str, Any]:
    """
    Metrics endpoint for monitoring systems.

    Returns comprehensive application metrics including:
    - Performance metrics
    - Business KPIs
    - Error rates
    - System health indicators

    Used by:
    - Prometheus/Grafana
    - Azure Monitor
    - Custom monitoring dashboards
    """
    monitoring = get_monitoring_service(settings)

    try:
        # Get comprehensive metrics
        health_metrics = await monitoring.get_health_metrics()
        metrics_export = await monitoring.get_metrics_export()

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": "ai-career-mentor",
            "version": settings.app_version,
            "environment": "production",  # TODO: Add environment field to settings
            "health": health_metrics,
            "detailed_metrics": metrics_export.get("metrics", {}),
            "collection_status": {
                "enabled": True,
                "application_insights": bool(
                    settings.azure_application_insights_connection_string
                ),
                "in_memory_fallback": True,
            },
        }

    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=503, detail="Metrics temporarily unavailable")


@router.get("/health/ready")
async def readiness_probe(
    settings: Settings = Depends(get_settings_dependency),
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
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            raise HTTPException(
                status_code=503, detail="Service not ready - dependencies unavailable"
            )

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")
