"""
Monitoring alerts and notification system.

This module provides:
- Threshold-based alerting
- Performance degradation detection
- Error rate monitoring
- Business metric alerts
- Notification delivery
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import structlog

from src.config.settings import Settings
from src.services.monitoring_service import MonitoringService


logger = structlog.get_logger()


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class AlertRule:
    """Definition of a monitoring alert rule."""

    name: str
    description: str
    metric_name: str
    threshold: float
    comparison: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    severity: AlertSeverity
    duration_minutes: int = 5  # How long condition must persist
    tags: Optional[Dict[str, str]] = None


@dataclass
class Alert:
    """An active alert instance."""

    id: str
    rule: AlertRule
    current_value: float
    status: AlertStatus
    fired_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    message: str = ""
    additional_data: Optional[Dict[str, Any]] = None


class MonitoringAlertsService:
    """
    Service for monitoring-based alerting and notifications.

    Provides:
    - Configurable alert rules
    - Threshold monitoring
    - Alert lifecycle management
    - Notification delivery
    """

    def __init__(self, settings: Settings, monitoring_service: MonitoringService):
        self.settings = settings
        self.monitoring = monitoring_service
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_handlers: List[Callable] = []

        # Setup default alert rules
        self._setup_default_alert_rules()

        # Start monitoring loop
        self._monitoring_task = None
        self._is_monitoring = False

    def _setup_default_alert_rules(self):
        """Setup default alert rules for common issues."""

        # High error rate alert
        self.alert_rules.append(
            AlertRule(
                name="high_error_rate",
                description="Error rate exceeds 5%",
                metric_name="error_rate_percentage",
                threshold=5.0,
                comparison="gt",
                severity=AlertSeverity.WARNING,
                duration_minutes=2,
            )
        )

        # Critical error rate alert
        self.alert_rules.append(
            AlertRule(
                name="critical_error_rate",
                description="Error rate exceeds 15%",
                metric_name="error_rate_percentage",
                threshold=15.0,
                comparison="gt",
                severity=AlertSeverity.CRITICAL,
                duration_minutes=1,
            )
        )

        # High response time alert
        self.alert_rules.append(
            AlertRule(
                name="high_response_time",
                description="Average response time exceeds 5 seconds",
                metric_name="avg_response_time_ms",
                threshold=5000.0,
                comparison="gt",
                severity=AlertSeverity.WARNING,
                duration_minutes=3,
            )
        )

        # Critical response time alert
        self.alert_rules.append(
            AlertRule(
                name="critical_response_time",
                description="Average response time exceeds 10 seconds",
                metric_name="avg_response_time_ms",
                threshold=10000.0,
                comparison="gt",
                severity=AlertSeverity.CRITICAL,
                duration_minutes=1,
            )
        )

        # Low success rate alert
        self.alert_rules.append(
            AlertRule(
                name="low_success_rate",
                description="Success rate below 95%",
                metric_name="success_rate_percentage",
                threshold=95.0,
                comparison="lt",
                severity=AlertSeverity.WARNING,
                duration_minutes=5,
            )
        )

        # AI service unavailable
        self.alert_rules.append(
            AlertRule(
                name="ai_service_down",
                description="Azure OpenAI service unavailable",
                metric_name="ai_service_health",
                threshold=0.0,
                comparison="eq",
                severity=AlertSeverity.CRITICAL,
                duration_minutes=1,
            )
        )

        # High token usage alert
        self.alert_rules.append(
            AlertRule(
                name="high_token_usage",
                description="Token usage exceeds 100k per hour",
                metric_name="tokens_per_hour",
                threshold=100000.0,
                comparison="gt",
                severity=AlertSeverity.INFO,
                duration_minutes=10,
            )
        )

        logger.info("Default alert rules configured", rules_count=len(self.alert_rules))

    def add_alert_rule(self, rule: AlertRule):
        """Add a custom alert rule."""
        self.alert_rules.append(rule)
        logger.info(
            "Alert rule added",
            rule_name=rule.name,
            metric=rule.metric_name,
            threshold=rule.threshold,
        )

    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule by name."""
        self.alert_rules = [r for r in self.alert_rules if r.name != rule_name]
        logger.info("Alert rule removed", rule_name=rule_name)

    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """Add a notification handler function."""
        self.notification_handlers.append(handler)

    async def start_monitoring(self):
        """Start the monitoring and alerting loop."""
        if self._is_monitoring:
            return

        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Alert monitoring started")

    async def stop_monitoring(self):
        """Stop the monitoring and alerting loop."""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Alert monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop that checks alert rules."""
        while self._is_monitoring:
            try:
                await self._check_alert_rules()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(60)  # Back off on errors

    async def _check_alert_rules(self):
        """Check all alert rules against current metrics."""
        try:
            # Get current metrics
            health_metrics = await self.monitoring.get_health_metrics()
            metrics_export = await self.monitoring.get_metrics_export()

            # Calculate derived metrics
            current_metrics = self._calculate_derived_metrics(
                health_metrics, metrics_export
            )

            # Check each rule
            for rule in self.alert_rules:
                await self._evaluate_rule(rule, current_metrics)

        except Exception as e:
            logger.error("Failed to check alert rules", error=str(e))

    def _calculate_derived_metrics(
        self, health_metrics: Dict[str, Any], metrics_export: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate derived metrics for alert evaluation."""
        try:
            metrics = metrics_export.get("metrics", {})
            counters = metrics.get("counters", {})
            histograms = metrics.get("histogram_summaries", {})

            # Calculate error rate
            total_requests = sum(
                count
                for name, count in counters.items()
                if "chat_requests_total" in str(name)
            )

            errors = sum(
                count for name, count in counters.items() if "errors_total" in str(name)
            )

            error_rate = (errors / total_requests * 100) if total_requests > 0 else 0.0
            success_rate = 100.0 - error_rate

            # Calculate average response time
            avg_response_time = 0.0
            for name, hist in histograms.items():
                if "response_time" in str(name) or "duration" in str(name):
                    avg_response_time = hist.get("avg", 0.0)
                    break

            # AI service health (0 = down, 1 = up)
            ai_service_health = 1.0  # This would come from actual health check

            # Token usage per hour (simplified calculation)
            tokens_per_hour = sum(
                count
                for name, count in counters.items()
                if "ai_tokens_used_total" in str(name)
            )

            return {
                "error_rate_percentage": error_rate,
                "success_rate_percentage": success_rate,
                "avg_response_time_ms": avg_response_time,
                "ai_service_health": ai_service_health,
                "tokens_per_hour": tokens_per_hour,
                "total_requests": total_requests,
                "total_errors": errors,
            }

        except Exception as e:
            logger.error("Failed to calculate derived metrics", error=str(e))
            return {}

    async def _evaluate_rule(self, rule: AlertRule, current_metrics: Dict[str, float]):
        """Evaluate a single alert rule."""
        try:
            metric_value = current_metrics.get(rule.metric_name)
            if metric_value is None:
                return

            # Check if threshold is breached
            threshold_breached = self._check_threshold(
                metric_value, rule.threshold, rule.comparison
            )

            alert_id = f"{rule.name}_{rule.metric_name}"
            existing_alert = self.active_alerts.get(alert_id)

            if threshold_breached:
                if existing_alert is None:
                    # Start tracking potential alert
                    alert = Alert(
                        id=alert_id,
                        rule=rule,
                        current_value=metric_value,
                        status=AlertStatus.ACTIVE,
                        fired_at=datetime.utcnow(),
                        message=f"{rule.description}. Current value: {metric_value}, Threshold: {rule.threshold}",
                    )

                    self.active_alerts[alert_id] = alert

                    # Fire alert immediately for critical issues
                    if rule.severity == AlertSeverity.CRITICAL:
                        await self._fire_alert(alert)
                    else:
                        logger.info(
                            "Alert condition detected, monitoring duration",
                            rule_name=rule.name,
                            current_value=metric_value,
                            threshold=rule.threshold,
                        )
                else:
                    # Update existing alert
                    existing_alert.current_value = metric_value

                    # Check if alert should fire based on duration
                    time_since_detection = datetime.utcnow() - existing_alert.fired_at
                    if (
                        time_since_detection.total_seconds()
                        >= rule.duration_minutes * 60
                    ):
                        if existing_alert.status == AlertStatus.ACTIVE and not hasattr(
                            existing_alert, "_notified"
                        ):
                            await self._fire_alert(existing_alert)
                            existing_alert._notified = True
            else:
                # Threshold not breached - resolve alert if exists
                if existing_alert and existing_alert.status == AlertStatus.ACTIVE:
                    await self._resolve_alert(existing_alert)

        except Exception as e:
            logger.error(
                "Failed to evaluate alert rule", rule_name=rule.name, error=str(e)
            )

    def _check_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """Check if a value breaches a threshold."""
        if comparison == "gt":
            return value > threshold
        elif comparison == "gte":
            return value >= threshold
        elif comparison == "lt":
            return value < threshold
        elif comparison == "lte":
            return value <= threshold
        elif comparison == "eq":
            return value == threshold
        else:
            return False

    async def _fire_alert(self, alert: Alert):
        """Fire an alert and send notifications."""
        logger.warning(
            "Alert fired",
            alert_id=alert.id,
            rule_name=alert.rule.name,
            severity=alert.rule.severity.value,
            current_value=alert.current_value,
            threshold=alert.rule.threshold,
            message=alert.message,
        )

        # Send notifications
        for handler in self.notification_handlers:
            try:
                await self._safe_notify(handler, alert)
            except Exception as e:
                logger.error("Notification handler failed", error=str(e))

        # Record business metric
        self.monitoring.record_business_metric(
            "alerts_fired_total",
            1.0,
            tags={"severity": alert.rule.severity.value, "rule_name": alert.rule.name},
        )

    async def _resolve_alert(self, alert: Alert):
        """Resolve an active alert."""
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()

        logger.info(
            "Alert resolved",
            alert_id=alert.id,
            rule_name=alert.rule.name,
            duration_minutes=(alert.resolved_at - alert.fired_at).total_seconds() / 60,
        )

        # Move to history and remove from active
        self.alert_history.append(alert)
        del self.active_alerts[alert.id]

        # Trim history to last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]

    async def _safe_notify(self, handler: Callable, alert: Alert):
        """Safely call a notification handler."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(alert)
            else:
                handler(alert)
        except Exception as e:
            logger.error("Notification handler error", error=str(e))

    def get_active_alerts(self) -> List[Alert]:
        """Get all currently active alerts."""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 50) -> List[Alert]:
        """Get recent alert history."""
        return self.alert_history[-limit:]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an active alert."""
        alert = self.active_alerts.get(alert_id)
        if alert:
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by

            logger.info(
                "Alert acknowledged", alert_id=alert_id, acknowledged_by=acknowledged_by
            )

    async def get_alerts_summary(self) -> Dict[str, Any]:
        """Get a summary of the alerting system status."""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "monitoring_enabled": self._is_monitoring,
            "alert_rules_count": len(self.alert_rules),
            "active_alerts_count": len(self.active_alerts),
            "alerts_by_severity": {
                severity.value: sum(
                    1
                    for alert in self.active_alerts.values()
                    if alert.rule.severity == severity
                )
                for severity in AlertSeverity
            },
            "recent_alerts_count": len(self.alert_history),
            "notification_handlers_count": len(self.notification_handlers),
        }


# Default notification handlers
async def log_notification_handler(alert: Alert):
    """Default notification handler that logs alerts."""
    logger.warning(
        "ALERT NOTIFICATION",
        alert_id=alert.id,
        rule_name=alert.rule.name,
        severity=alert.rule.severity.value,
        message=alert.message,
        current_value=alert.current_value,
        threshold=alert.rule.threshold,
    )


async def webhook_notification_handler(alert: Alert, webhook_url: str):
    """Notification handler that sends alerts to a webhook."""
    import httpx

    try:
        payload = {
            "alert_id": alert.id,
            "rule_name": alert.rule.name,
            "severity": alert.rule.severity.value,
            "message": alert.message,
            "current_value": alert.current_value,
            "threshold": alert.rule.threshold,
            "fired_at": alert.fired_at.isoformat(),
            "status": alert.status.value,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

        logger.info("Alert sent to webhook", alert_id=alert.id, webhook=webhook_url)

    except Exception as e:
        logger.error(
            "Failed to send webhook notification", alert_id=alert.id, error=str(e)
        )
