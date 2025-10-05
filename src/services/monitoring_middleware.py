"""
Monitoring middleware for FastAPI applications.

This middleware automatically tracks:
- Request/response metrics
- Performance timing
- Error rates
- Business KPIs
"""

import time
from typing import Callable, Optional
try:
    from fastapi import FastAPI, Request, Response
    from fastapi.middleware.base import BaseHTTPMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Provide stub for type hints
    FastAPI = None
    Request = None
    Response = None
    BaseHTTPMiddleware = object

import structlog

from src.services.monitoring_service import get_monitoring_service
from src.config.settings import get_settings_dependency


logger = structlog.get_logger()


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic request monitoring and metrics collection.
    
    Tracks:
    - Request count and response status codes
    - Response times and performance metrics
    - Error rates and exception tracking
    - Business metrics and user analytics
    """
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.settings = get_settings_dependency()
        self.monitoring = get_monitoring_service(self.settings)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect monitoring metrics."""
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        endpoint = f"{method} {path}"
        
        # Generate request ID for tracing
        request_id = getattr(request.state, 'request_id', None)
        if not request_id:
            import uuid
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
        
        # Log request start
        logger.info(
            "Request started",
            method=method,
            path=path,
            request_id=request_id,
            user_agent=request.headers.get("user-agent", "unknown"),
            client_host=request.client.host if request.client else "unknown"
        )
        
        # Process request and handle errors
        response = None
        error_occurred = False
        error_type = None
        
        try:
            # Use monitoring context for request tracing
            async with self.monitoring.trace_request(
                operation_name=endpoint,
                request_id=request_id,
                method=method,
                path=path
            ) as trace_context:
                # Add trace context to request state
                request.state.trace_context = trace_context
                
                # Call the actual endpoint
                response = await call_next(request)
                
                # Determine status from response
                status_code = response.status_code
                status = "success" if 200 <= status_code < 400 else "error"
                
        except Exception as e:
            error_occurred = True
            error_type = type(e).__name__
            status = "error"
            status_code = 500
            
            # Record error metrics
            self.monitoring.record_error(
                error_type=error_type,
                endpoint=endpoint,
                error_message=str(e),
                user_id=request_id
            )
            
            logger.error(
                "Request failed",
                method=method,
                path=path,
                request_id=request_id,
                error=str(e),
                error_type=error_type
            )
            
            # Re-raise the exception to be handled by FastAPI
            raise
        
        finally:
            # Calculate response time
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            if not error_occurred and response:
                status_code = response.status_code
                status = "success" if 200 <= status_code < 400 else "error"
                
                # Record successful request metrics
                self.monitoring.record_chat_request(
                    endpoint=endpoint,
                    status=status,
                    response_time_ms=response_time_ms,
                    user_id=request_id
                )
                
                # Add monitoring headers to response
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
                
                logger.info(
                    "Request completed",
                    method=method,
                    path=path,
                    request_id=request_id,
                    status_code=status_code,
                    response_time_ms=response_time_ms
                )
        
        return response


def add_monitoring_middleware(app: FastAPI):
    """
    Add monitoring middleware to FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(MonitoringMiddleware)
    logger.info("Monitoring middleware added to FastAPI application")


class ChatMetricsCollector:
    """Specialized metrics collector for chat-specific business KPIs."""
    
    def __init__(self, monitoring_service):
        self.monitoring = monitoring_service
    
    def record_chat_interaction(self,
                              user_message: str,
                              ai_response: str,
                              response_time_ms: float,
                              token_usage: dict,
                              session_id: str,
                              user_satisfaction: Optional[int] = None):
        """
        Record comprehensive chat interaction metrics.
        
        Args:
            user_message: User's input message
            ai_response: AI's response
            response_time_ms: Time to generate response
            token_usage: Token consumption details
            session_id: Chat session identifier
            user_satisfaction: Optional satisfaction rating (1-5)
        """
        # Record basic chat metrics
        self.monitoring.record_chat_request(
            endpoint="POST /api/chat",
            status="success",
            response_time_ms=response_time_ms,
            token_usage=token_usage,
            user_id=session_id
        )
        
        # Record business-specific metrics
        self.monitoring.record_business_metric(
            "message_length_chars",
            len(user_message),
            tags={"type": "user_input"}
        )
        
        self.monitoring.record_business_metric(
            "response_length_chars", 
            len(ai_response),
            tags={"type": "ai_response"}
        )
        
        if user_satisfaction:
            self.monitoring.record_business_metric(
                "user_satisfaction_score",
                user_satisfaction,
                tags={"session_type": "chat"}
            )
        
        # Log chat analytics
        logger.info(
            "Chat interaction completed",
            session_id=session_id,
            user_message_length=len(user_message),
            ai_response_length=len(ai_response),
            response_time_ms=response_time_ms,
            tokens_used=token_usage.get("total_tokens", 0),
            user_satisfaction=user_satisfaction
        )
    
    def record_rag_search(self,
                         query: str,
                         documents_found: int,
                         search_time_ms: float,
                         session_id: str):
        """
        Record RAG system search metrics.
        
        Args:
            query: Search query text
            documents_found: Number of relevant documents found
            search_time_ms: Time to execute search
            session_id: Chat session identifier
        """
        self.monitoring.record_search_query(
            query=query,
            results_count=documents_found,
            search_time_ms=search_time_ms,
            user_id=session_id
        )
        
        # Record search quality metrics
        self.monitoring.record_business_metric(
            "search_relevance_score",
            min(documents_found / 5.0, 1.0),  # Normalize to 0-1 scale
            tags={"search_type": "rag"}
        )
    
    def record_session_metrics(self,
                             session_id: str,
                             action: str,
                             messages_count: Optional[int] = None,
                             session_duration_minutes: Optional[float] = None):
        """
        Record user session metrics and behavior.
        
        Args:
            session_id: Session identifier
            action: Session action (start, end, message)
            messages_count: Total messages in session
            session_duration_minutes: Session duration in minutes
        """
        self.monitoring.record_user_session(session_id, action)
        
        if action == "end" and messages_count:
            self.monitoring.record_business_metric(
                "session_message_count",
                messages_count,
                tags={"completion_type": "natural_end"}
            )
        
        if session_duration_minutes:
            self.monitoring.record_business_metric(
                "session_duration_minutes",
                session_duration_minutes,
                tags={"completion_type": "natural_end"}
            )
        
        logger.info(
            "Session metrics recorded",
            session_id=session_id,
            action=action,
            messages_count=messages_count,
            duration_minutes=session_duration_minutes
        )