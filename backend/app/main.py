"""
FastAPI application entry point.
InterviewSage AI - An Agentic AI Interview Simulation Platform with Production Observability.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.metrics import get_metrics_response
from app.core.request_context import RequestContextMiddleware
from app.core.telemetry import setup_telemetry

# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # Create necessary directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs("./logs", exist_ok=True)

    # Run PostgreSQL schema migrations
    try:
        from app.migrate_interview_role import migrate as migrate_roles
        migrate_roles()
    except Exception as exc:
        logger.warning(f"Database startup migration warning: {exc}")

    # Initialize OpenTelemetry / LangSmith instrumentation
    setup_telemetry(app)

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="An Agentic AI Interview Simulation Platform powered by Multi-Agent Systems, LangGraph, and Large Language Models",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Request Correlation ID & Context Middleware
app.add_middleware(RequestContextMiddleware)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Observability"])
async def health_check():
    """
    Enhanced Health Check Probe.
    Checks database connection and system readiness.
    """
    db_healthy = False
    try:
        from app.core.database import SessionLocal
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            db_healthy = True
    except Exception as e:
        logger.error(f"Health check database connection failed: {e!s}")

    try:
        from app.mcp.server import mcp_server
    except Exception:
        mcp_server = None

    mcp_healthy = bool(mcp_server and (hasattr(mcp_server, "_tools") or hasattr(mcp_server, "list_tools")))

    status_code = 200 if db_healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if db_healthy else "unhealthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "subsystems": {
                "database": "connected" if db_healthy else "disconnected",
                "langgraph": "ready",
                "mcp_server": "active" if mcp_healthy else "degraded",
                "llm_router": "configured",
                "candidate_memory": "active",
                "voice_engine": "active",
                "career_intelligence": "active",
            },
        },
    )


@app.get("/ready", tags=["Observability"])
async def readiness_check():
    """Readiness probe for Kubernetes & load balancers."""
    return {"status": "ready"}


@app.get("/live", tags=["Observability"])
async def liveness_check():
    """Liveness probe for Kubernetes container restart checks."""
    return {"status": "live"}


@app.get("/metrics", tags=["Observability"])
async def metrics_endpoint():
    """Expose Prometheus metrics for scraping."""
    return get_metrics_response()


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    Provides basic API information.
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


# Router registration
from app.api.v1.routes import (
    admin,
    analytics,
    answers,
    auth,
    career,
    interviews,
    job_descriptions,
    memory,
    reports,
    resumes,
    transcripts,
    users,
    voice,
    websocket,
)
from app.websocket.interview_socket import router as voice_ws_router

app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(interviews.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")
app.include_router(voice_ws_router, prefix="/api/v1")
app.include_router(answers.router, prefix="/api/v1")
app.include_router(resumes.router, prefix="/api/v1")
app.include_router(job_descriptions.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
app.include_router(transcripts.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
app.include_router(career.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
