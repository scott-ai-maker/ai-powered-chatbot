"""
Monitoring and observability service for comprehensive application monitoring.

This service provides:
- Custom metrics and performance tracking
- Health monitoring and alerting
- Business metrics and KPIs
- Error tracking and diagnostics
- Azure Application Insights integration (when available)
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import hashlib
from collections import defaultdict, deque

import structlog

from src.config.settings import Settings


logger = structlog.get_logger()


class MetricsCollector:
    """In-memory metrics collector for development and fallback scenarios."""

    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(lambda: deque(maxlen=1000))
        self.gauges = defaultdict(float)
        self.start_time = datetime.utcnow()

    def increment_counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric."""
        key = self._make_key(name, tags)
        self.counters[key] += value

    def record_histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a histogram value."""
        key = self._make_key(name, tags)
        self.histograms[key].append({"value": value, "timestamp": datetime.utcnow()})

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge value."""
        key = self._make_key(name, tags)
        self.gauges[key] = value

    def _make_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Create a unique key for the metric."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics."""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histogram_summaries": {
                name: {
                    "count": len(values),
                    "avg": sum(v["value"] for v in values) / len(values)
                    if values
                    else 0,
                    "min": min(v["value"] for v in values) if values else 0,
                    "max": max(v["value"] for v in values) if values else 0,
                }
                for name, values in self.histograms.items()
            },
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
        }


class MonitoringService:
    """
    Comprehensive monitoring service for application observability.

    Provides metrics, tracing, logging, and custom business KPIs.
    Supports both Azure Application Insights and in-memory fallback.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.metrics = MetricsCollector()

        # Track application start time
        self.start_time = datetime.utcnow()

        # Initialize Application Insights if configured
        self.app_insights_enabled = bool(
            settings.azure_application_insights_connection_string
        )

        if self.app_insights_enabled:
            self._setup_application_insights()
        else:
            logger.info("Application Insights not configured, using in-memory metrics")

    def _setup_application_insights(self):
        """Setup Azure Application Insights integration."""
        try:
            # This would integrate with Azure Monitor when dependencies are available
            # For now, we log that it's configured
            logger.info(
                "Application Insights configured", connection_string_configured=True
            )

        except Exception as e:
            logger.error("Failed to setup Application Insights", error=str(e))
            self.app_insights_enabled = False

    @asynccontextmanager
    async def trace_request(self, operation_name: str, **properties):
        """
        Context manager for tracing requests with custom properties.

        Args:
            operation_name: Name of the operation being traced
            **properties: Additional properties to attach to the trace
        """
        start_time = time.time()
        trace_id = str(uuid.uuid4())

        logger.info(
            "Operation started",
            operation=operation_name,
            trace_id=trace_id,
            **properties,
        )

        try:
            yield {"trace_id": trace_id, "operation": operation_name}
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            # Record error metrics
            self.metrics.increment_counter(
                "operation_errors_total",
                tags={"operation": operation_name, "error_type": type(e).__name__},
            )

            logger.error(
                "Operation failed",
                operation=operation_name,
                trace_id=trace_id,
                duration_ms=duration_ms,
                error=str(e),
                **properties,
            )
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000

            # Record timing metrics
            self.metrics.record_histogram(
                "operation_duration_ms", duration_ms, tags={"operation": operation_name}
            )

            logger.info(
                "Operation completed",
                operation=operation_name,
                trace_id=trace_id,
                duration_ms=duration_ms,
                **properties,
            )

    def record_chat_request(
        self,
        endpoint: str,
        status: str,
        response_time_ms: float,
        token_usage: Optional[Dict[str, int]] = None,
        user_id: Optional[str] = None,
    ):
        """
        Record metrics for chat requests.

        Args:
            endpoint: API endpoint called
            status: Request status (success, error, etc.)
            response_time_ms: Response time in milliseconds
            token_usage: Token usage breakdown
            user_id: User identifier (hashed for privacy)
        """
        # Record request count
        self.metrics.increment_counter(
            "chat_requests_total", tags={"endpoint": endpoint, "status": status}
        )

        # Record response time
        self.metrics.record_histogram(
            "chat_response_time_ms", response_time_ms, tags={"endpoint": endpoint}
        )

        # Record token usage if provided
        if token_usage:
            for token_type, count in token_usage.items():
                if token_type in ["prompt_tokens", "completion_tokens", "total_tokens"]:
                    self.metrics.increment_counter(
                        "ai_tokens_used_total",
                        value=count,
                        tags={
                            "model": str(token_usage.get("model", "unknown")),
                            "type": token_type,
                        },
                    )

        # Hash user ID for privacy
        user_hash = None
        if user_id:
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]

        # Log business metrics
        logger.info(
            "Chat request completed",
            endpoint=endpoint,
            status=status,
            response_time_ms=response_time_ms,
            token_usage=token_usage,
            user_id_hash=user_hash,
        )

    def record_search_query(
        self,
        query: str,
        results_count: int,
        search_time_ms: float,
        user_id: Optional[str] = None,
    ):
        """Record metrics for search queries."""
        # Record search count
        self.metrics.increment_counter(
            "search_queries_total", tags={"type": "knowledge_search"}
        )

        # Record search timing
        self.metrics.record_histogram(
            "search_duration_ms", search_time_ms, tags={"type": "knowledge_search"}
        )

        # Record result count
        self.metrics.record_histogram(
            "search_results_count", results_count, tags={"type": "knowledge_search"}
        )

        # Hash user ID for privacy
        user_hash = None
        if user_id:
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]

        # Log search analytics
        logger.info(
            "Search query executed",
            query_length=len(query),
            results_count=results_count,
            search_time_ms=search_time_ms,
            user_id_hash=user_hash,
        )

    def record_error(
        self,
        error_type: str,
        endpoint: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Record error metrics and logging."""
        # Record error count
        self.metrics.increment_counter(
            "errors_total", tags={"error_type": error_type, "endpoint": endpoint}
        )

        # Hash user ID for privacy
        user_hash = None
        if user_id:
            user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:8]

        # Log error details
        logger.error(
            "Application error occurred",
            error_type=error_type,
            endpoint=endpoint,
            error_message=error_message,
            stack_trace=stack_trace,
            user_id_hash=user_hash,
        )

    def record_business_metric(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """
        Record custom business metrics.

        Args:
            metric_name: Name of the business metric
            value: Metric value
            tags: Optional tags for categorization
        """
        # Record as gauge metric
        self.metrics.set_gauge(metric_name, value, tags)

        logger.info(
            "Business metric recorded",
            metric_name=metric_name,
            value=value,
            tags=tags or {},
        )

    def record_user_session(self, session_id: str, action: str):
        """
        Record user session metrics.

        Args:
            session_id: Session identifier (will be hashed)
            action: Action taken (start, end, activity)
        """
        session_hash = hashlib.sha256(session_id.encode()).hexdigest()[:8]

        self.metrics.increment_counter("user_sessions_total", tags={"action": action})

        logger.info("User session event", session_hash=session_hash, action=action)

    async def get_health_metrics(self) -> Dict[str, Any]:
        """
        Get current health and performance metrics.

        Returns:
            Dictionary containing current system health metrics
        """
        try:
            current_time = datetime.utcnow()
            uptime_seconds = (current_time - self.start_time).total_seconds()

            # Get metrics summary
            metrics_summary = self.metrics.get_metrics_summary()

            return {
                "timestamp": current_time.isoformat() + "Z",
                "monitoring_enabled": True,
                "service_status": "healthy",
                "uptime_seconds": uptime_seconds,
                "uptime_hours": uptime_seconds / 3600,
                "metrics_collection": {
                    "chat_requests": "enabled",
                    "response_times": "enabled",
                    "token_usage": "enabled",
                    "error_tracking": "enabled",
                    "search_analytics": "enabled",
                    "business_metrics": "enabled",
                },
                "integration_status": {
                    "application_insights": self.app_insights_enabled,
                    "structured_logging": True,
                    "in_memory_metrics": True,
                },
                "metrics_summary": {
                    "total_counters": len(metrics_summary["counters"]),
                    "total_gauges": len(metrics_summary["gauges"]),
                    "total_histograms": len(metrics_summary["histogram_summaries"]),
                    "sample_metrics": {
                        "chat_requests": sum(
                            count
                            for name, count in metrics_summary["counters"].items()
                            if "chat_requests_total" in name
                        ),
                        "errors": sum(
                            count
                            for name, count in metrics_summary["counters"].items()
                            if "errors_total" in name
                        ),
                    },
                },
            }

        except Exception as e:
            logger.error("Failed to get health metrics", error=str(e))
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "error",
                "error": str(e),
            }

    async def get_metrics_export(self) -> Dict[str, Any]:
        """
        Export all collected metrics for external monitoring systems.

        Returns:
            Dictionary containing all metrics data
        """
        try:
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "service": "ai-career-mentor",
                "version": "1.0.0",
                "metrics": self.metrics.get_metrics_summary(),
            }
        except Exception as e:
            logger.error("Failed to export metrics", error=str(e))
            return {"error": str(e)}

    async def flush_metrics(self):
        """Flush pending metrics to external systems."""
        try:
            if self.app_insights_enabled:
                # In a real implementation, this would flush to Application Insights
                logger.debug("Would flush metrics to Application Insights")

            # Log current metrics summary
            metrics_summary = self.metrics.get_metrics_summary()
            logger.info(
                "Metrics flushed",
                counters_count=len(metrics_summary["counters"]),
                gauges_count=len(metrics_summary["gauges"]),
                histograms_count=len(metrics_summary["histogram_summaries"]),
            )

        except Exception as e:
            logger.error("Failed to flush metrics", error=str(e))


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service(settings: Settings) -> MonitoringService:
    """Get or create monitoring service instance."""
    global _monitoring_service

    if _monitoring_service is None:
        _monitoring_service = MonitoringService(settings)

    return _monitoring_service


def get_monitoring_dependency(settings: Optional[Settings] = None) -> MonitoringService:
    """FastAPI dependency for monitoring service."""
    from src.config.settings import get_settings_dependency

    if settings is None:
        settings = get_settings_dependency()

    return get_monitoring_service(settings)
