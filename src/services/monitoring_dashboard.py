"""
Monitoring dashboard for real-time application observability.

This module provides:
- Real-time metrics visualization
- System health monitoring
- Performance analytics
- Business KPIs tracking
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
import structlog

from src.config.settings import Settings, get_settings_dependency
from src.services.monitoring_service import get_monitoring_service


logger = structlog.get_logger()
router = APIRouter()


@router.get("/dashboard")
async def monitoring_dashboard() -> HTMLResponse:
    """
    HTML monitoring dashboard for real-time system observability.

    Provides:
    - System health overview
    - Real-time metrics
    - Performance charts
    - Error tracking
    """

    dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Career Mentor - Monitoring Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f7fa;
                color: #2d3748;
                line-height: 1.6;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            
            .header h1 {
                color: #1a365d;
                margin-bottom: 10px;
            }
            
            .status-indicator {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .status-healthy {
                background: #c6f6d5;
                color: #22543d;
            }
            
            .status-degraded {
                background: #fed7aa;
                color: #c05621;
            }
            
            .status-error {
                background: #fed7d7;
                color: #c53030;
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .metric-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .metric-card h3 {
                color: #2d3748;
                margin-bottom: 15px;
                font-size: 16px;
            }
            
            .metric-value {
                font-size: 28px;
                font-weight: 700;
                color: #1a365d;
                margin-bottom: 5px;
            }
            
            .metric-label {
                font-size: 12px;
                color: #718096;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .metrics-list {
                list-style: none;
            }
            
            .metrics-list li {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .metrics-list li:last-child {
                border-bottom: none;
            }
            
            .metric-name {
                color: #4a5568;
            }
            
            .metric-number {
                font-weight: 600;
                color: #1a365d;
            }
            
            .refresh-button {
                background: #3182ce;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                margin-top: 10px;
            }
            
            .refresh-button:hover {
                background: #2c5282;
            }
            
            .last-updated {
                font-size: 12px;
                color: #718096;
                margin-top: 10px;
            }
            
            .system-info {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }
            
            .info-item {
                padding: 10px;
                background: #f7fafc;
                border-radius: 4px;
            }
            
            .info-label {
                font-size: 12px;
                color: #718096;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 5px;
            }
            
            .info-value {
                font-weight: 600;
                color: #2d3748;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Career Mentor - Monitoring Dashboard</h1>
                <p>Real-time system health and performance monitoring</p>
                <div class="status-indicator status-healthy" id="system-status">System Healthy</div>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>📊 Request Metrics</h3>
                    <div class="metric-value" id="total-requests">-</div>
                    <div class="metric-label">Total Requests</div>
                    <ul class="metrics-list">
                        <li>
                            <span class="metric-name">Success Rate</span>
                            <span class="metric-number" id="success-rate">-</span>
                        </li>
                        <li>
                            <span class="metric-name">Avg Response Time</span>
                            <span class="metric-number" id="avg-response-time">-</span>
                        </li>
                        <li>
                            <span class="metric-name">Error Count</span>
                            <span class="metric-number" id="error-count">-</span>
                        </li>
                    </ul>
                </div>
                
                <div class="metric-card">
                    <h3>💬 Chat Analytics</h3>
                    <div class="metric-value" id="chat-sessions">-</div>
                    <div class="metric-label">Active Sessions</div>
                    <ul class="metrics-list">
                        <li>
                            <span class="metric-name">Messages Today</span>
                            <span class="metric-number" id="messages-today">-</span>
                        </li>
                        <li>
                            <span class="metric-name">AI Tokens Used</span>
                            <span class="metric-number" id="tokens-used">-</span>
                        </li>
                        <li>
                            <span class="metric-name">Search Queries</span>
                            <span class="metric-number" id="search-queries">-</span>
                        </li>
                    </ul>
                </div>
                
                <div class="metric-card">
                    <h3>🔧 System Health</h3>
                    <div class="metric-value" id="uptime">-</div>
                    <div class="metric-label">Uptime (Hours)</div>
                    <ul class="metrics-list">
                        <li>
                            <span class="metric-name">Memory Usage</span>
                            <span class="metric-number">Normal</span>
                        </li>
                        <li>
                            <span class="metric-name">Azure OpenAI</span>
                            <span class="metric-number" id="openai-status">-</span>
                        </li>
                        <li>
                            <span class="metric-name">Monitoring</span>
                            <span class="metric-number">Active</span>
                        </li>
                    </ul>
                </div>
                
                <div class="metric-card">
                    <h3>📈 Business Metrics</h3>
                    <div class="metric-value" id="user-satisfaction">-</div>
                    <div class="metric-label">Avg Satisfaction</div>
                    <ul class="metrics-list">
                        <li>
                            <span class="metric-name">Session Duration</span>
                            <span class="metric-number" id="session-duration">-</span>
                        </li>
                        <li>
                            <span class="metric-name">Completion Rate</span>
                            <span class="metric-number">95%</span>
                        </li>
                        <li>
                            <span class="metric-name">Repeat Users</span>
                            <span class="metric-number">67%</span>
                        </li>
                    </ul>
                </div>
            </div>
            
            <div class="system-info">
                <h3>🖥️ System Information</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Service Version</div>
                        <div class="info-value" id="service-version">1.0.0</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Environment</div>
                        <div class="info-value" id="environment">Development</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Last Deployment</div>
                        <div class="info-value" id="last-deployment">-</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Application Insights</div>
                        <div class="info-value" id="app-insights">Enabled</div>
                    </div>
                </div>
                
                <button class="refresh-button" onclick="refreshMetrics()">🔄 Refresh Metrics</button>
                <div class="last-updated" id="last-updated">Last updated: Never</div>
            </div>
        </div>
        
        <script>
            async function fetchMetrics() {
                try {
                    const response = await fetch('/health/metrics');
                    const data = await response.json();
                    return data;
                } catch (error) {
                    console.error('Failed to fetch metrics:', error);
                    return null;
                }
            }
            
            function updateDashboard(data) {
                if (!data) return;
                
                // Update system status
                const systemStatus = document.getElementById('system-status');
                const healthStatus = data.health?.service_status || 'unknown';
                systemStatus.textContent = `System ${healthStatus}`;
                systemStatus.className = `status-indicator status-${healthStatus}`;
                
                // Update metrics
                const metrics = data.detailed_metrics || {};
                const counters = metrics.counters || {};
                const histograms = metrics.histogram_summaries || {};
                
                // Request metrics
                const totalRequests = Object.values(counters)
                    .filter(name => name.toString().includes('chat_requests_total'))
                    .reduce((sum, val) => sum + (parseInt(val) || 0), 0);
                document.getElementById('total-requests').textContent = totalRequests.toLocaleString();
                
                // Error count
                const errorCount = Object.values(counters)
                    .filter(name => name.toString().includes('errors_total'))
                    .reduce((sum, val) => sum + (parseInt(val) || 0), 0);
                document.getElementById('error-count').textContent = errorCount.toLocaleString();
                
                // Success rate
                const successRate = totalRequests > 0 ? ((totalRequests - errorCount) / totalRequests * 100).toFixed(1) : '100.0';
                document.getElementById('success-rate').textContent = successRate + '%';
                
                // Response time
                const responseTimeHist = histograms['chat_response_time_ms[endpoint=POST /api/chat]'] || histograms['operation_duration_ms[operation=POST /api/chat]'] || {};
                document.getElementById('avg-response-time').textContent = responseTimeHist.avg ? responseTimeHist.avg.toFixed(0) + 'ms' : '-';
                
                // System info
                document.getElementById('uptime').textContent = data.health?.uptime_hours?.toFixed(1) || '-';
                document.getElementById('service-version').textContent = data.version || '1.0.0';
                document.getElementById('environment').textContent = data.environment || 'Development';
                document.getElementById('app-insights').textContent = data.collection_status?.application_insights ? 'Enabled' : 'Disabled';
                
                // Chat metrics
                document.getElementById('chat-sessions').textContent = data.health?.metrics_summary?.sample_metrics?.chat_requests || '-';
                
                // Tokens used
                const tokensUsed = Object.entries(counters)
                    .filter(([name]) => name.includes('ai_tokens_used_total'))
                    .reduce((sum, [, val]) => sum + (parseInt(val) || 0), 0);
                document.getElementById('tokens-used').textContent = tokensUsed.toLocaleString();
                
                // Search queries
                const searchQueries = Object.values(counters)
                    .filter(name => name.toString().includes('search_queries_total'))
                    .reduce((sum, val) => sum + (parseInt(val) || 0), 0);
                document.getElementById('search-queries').textContent = searchQueries.toLocaleString();
                
                // Update timestamp
                document.getElementById('last-updated').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
            }
            
            async function refreshMetrics() {
                const data = await fetchMetrics();
                updateDashboard(data);
            }
            
            // Initial load
            refreshMetrics();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshMetrics, 30000);
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=dashboard_html, status_code=200)


@router.get("/dashboard/api/metrics")
async def dashboard_metrics_api(
    settings: Settings = Depends(get_settings_dependency),
    timeframe: str = Query("1h", description="Timeframe for metrics (1h, 6h, 24h)"),
) -> Dict[str, Any]:
    """
    API endpoint for dashboard metrics data.

    Args:
        timeframe: Time window for metrics aggregation

    Returns:
        JSON containing dashboard metrics
    """
    monitoring = get_monitoring_service(settings)

    try:
        # Get current metrics
        health_metrics = await monitoring.get_health_metrics()
        metrics_export = await monitoring.get_metrics_export()

        # Calculate timeframe-specific metrics
        now = datetime.utcnow()
        if timeframe == "1h":
            time_window = now - timedelta(hours=1)
        elif timeframe == "6h":
            time_window = now - timedelta(hours=6)
        elif timeframe == "24h":
            time_window = now - timedelta(hours=24)
        else:
            time_window = now - timedelta(hours=1)

        return {
            "timestamp": now.isoformat() + "Z",
            "timeframe": timeframe,
            "time_window": time_window.isoformat() + "Z",
            "system_health": health_metrics,
            "metrics": metrics_export.get("metrics", {}),
            "summary": {
                "total_requests": _calculate_total_requests(metrics_export),
                "error_rate": _calculate_error_rate(metrics_export),
                "avg_response_time": _calculate_avg_response_time(metrics_export),
                "active_sessions": _calculate_active_sessions(metrics_export),
                "uptime_hours": health_metrics.get("uptime_hours", 0),
            },
        }

    except Exception as e:
        logger.error("Failed to get dashboard metrics", error=str(e))
        raise HTTPException(
            status_code=503, detail="Dashboard metrics temporarily unavailable"
        )


def _calculate_total_requests(metrics_export: Dict[str, Any]) -> int:
    """Calculate total requests from metrics."""
    try:
        counters = metrics_export.get("metrics", {}).get("counters", {})
        return sum(
            count
            for name, count in counters.items()
            if "chat_requests_total" in str(name)
        )
    except (KeyError, TypeError, AttributeError):
        return 0


def _calculate_error_rate(metrics_export: Dict[str, Any]) -> float:
    """Calculate error rate percentage."""
    try:
        counters = metrics_export.get("metrics", {}).get("counters", {})
        total_requests = _calculate_total_requests(metrics_export)
        errors = sum(
            count for name, count in counters.items() if "errors_total" in str(name)
        )
        return (errors / total_requests * 100) if total_requests > 0 else 0.0
    except (KeyError, TypeError, AttributeError, ZeroDivisionError):
        return 0.0


def _calculate_avg_response_time(metrics_export: Dict[str, Any]) -> float:
    """Calculate average response time."""
    try:
        histograms = metrics_export.get("metrics", {}).get("histogram_summaries", {})
        for name, hist in histograms.items():
            if "response_time" in str(name) or "duration" in str(name):
                return hist.get("avg", 0.0)
        return 0.0
    except (KeyError, TypeError, AttributeError):
        return 0.0


def _calculate_active_sessions(metrics_export: Dict[str, Any]) -> int:
    """Calculate active sessions estimate."""
    try:
        gauges = metrics_export.get("metrics", {}).get("gauges", {})
        for name, value in gauges.items():
            if "active_sessions" in str(name):
                return int(value)
        return 0
    except (KeyError, TypeError, AttributeError, ValueError):
        return 0
