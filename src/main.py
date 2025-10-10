"""
Main FastAPI application entry point.

This module sets up the FastAPI application with proper async configuration,
middleware, exception handlers, and route registration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from src.config.settings import get_settings


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.

    This is the modern FastAPI way to handle startup/shutdown events.
    We'll use this to initialize Azure services, databases, etc.
    """
    settings = get_settings()

    # Startup
    logger.info(
        "Starting AI Career Mentor Chatbot",
        app_name=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # Initialize monitoring service - TEMPORARILY DISABLED
    # monitoring = get_monitoring_service(settings)
    # logger.info("Monitoring service initialized")
    # monitoring = None  # Temporarily disabled
    logger.warning("Monitoring service temporarily disabled")

    # Initialize Azure services
    from src.services.ai_service import AzureOpenAIService
    from src.services.search_service import AzureCognitiveSearchService
    from src.services.rag_service import RAGEnhancedAIService
    import src.api.endpoints.chat as chat_module

    try:
        # Initialize AI service globally
        if chat_module._ai_service is None:
            chat_module._ai_service = AzureOpenAIService(settings)
            await chat_module._ai_service.__aenter__()
            logger.info("Azure OpenAI service initialized")

        # Initialize search service and RAG service
        if chat_module._search_service is None:
            chat_module._search_service = AzureCognitiveSearchService(settings)
            await chat_module._search_service.initialize_index()
            logger.info("Azure Cognitive Search service initialized")

        if chat_module._rag_service is None:
            chat_module._rag_service = RAGEnhancedAIService(
                settings=settings, search_service=chat_module._search_service
            )
            logger.info("RAG-enhanced AI service initialized")

    except Exception as e:
        logger.error("Failed to initialize Azure services", error=str(e))
        # Don't fail startup - services will handle connection issues gracefully

    # Record startup metrics
    # monitoring.record_business_metric("application_starts", 1.0, tags={"version": settings.app_version})

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application")

    # Cleanup resources
    if chat_module._ai_service:
        try:
            await chat_module._ai_service.__aexit__(None, None, None)
            logger.info("AI service cleaned up")
        except Exception as e:
            logger.error("Error cleaning up AI service", error=str(e))

    if chat_module._search_service:
        try:
            await chat_module._search_service.close()
            logger.info("Search service cleaned up")
        except Exception as e:
            logger.error("Error cleaning up search service", error=str(e))

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This function follows the application factory pattern, which is
    useful for testing and allows for different configurations.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="An intelligent AI-powered chatbot for career guidance in AI engineering",
        docs_url="/docs" if settings.debug else None,  # Disable docs in production
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Configure monitoring middleware (before CORS) - TEMPORARILY DISABLED
    # try:
    #     from src.services.monitoring_middleware import add_monitoring_middleware
    #     add_monitoring_middleware(app)
    # except ImportError:
    #     logger.warning("Monitoring middleware not available - continuing without it")
    logger.warning("Monitoring middleware temporarily disabled")

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts_list if not settings.debug else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Custom exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with structured logging."""
        logger.warning(
            "HTTP exception occurred",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "status_code": exc.status_code},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions with structured logging."""
        logger.error(
            "Unexpected exception occurred",
            exception=str(exc),
            exception_type=type(exc).__name__,
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "status_code": 500},
        )

    # Middleware for request logging
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests with structured logging."""
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
        )

        response = await call_next(request)

        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )

        return response

    # Register routers
    from src.api.endpoints import chat, health

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

    # Add monitoring dashboard - TEMPORARILY DISABLED
    # try:
    #     from src.services.monitoring_dashboard import router as dashboard_router
    #     app.include_router(dashboard_router, prefix="/monitoring", tags=["monitoring"])
    #     logger.info("Monitoring dashboard registered")
    # except ImportError:
    #     logger.warning("Monitoring dashboard not available")
    logger.warning("Monitoring dashboard temporarily disabled")

    return app


# Create the app instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint for basic health check."""
    settings = get_settings()
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "healthy",
    }


if __name__ == "__main__":
    # This allows running the app with: python -m src.main
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
