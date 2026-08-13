"""
OpenTelemetry and LangSmith Observability Integration for InterviewSage AI.
Configures tracing for FastAPI, SQLAlchemy, and LangGraph workflows with graceful fallbacks.
"""

from __future__ import annotations

import os
from typing import Any, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_telemetry(app: Optional[Any] = None) -> None:
    """
    Initialize OpenTelemetry and LangSmith tracing if enabled in environment.
    """
    # LangSmith Tracing Setup
    if os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true":
        logger.info("LangSmith Tracing (v2) Enabled.")
    else:
        logger.info("LangSmith Tracing not configured. Continuing with standard execution.")

    # OpenTelemetry Tracing Setup
    try:
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        if app is not None:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("OpenTelemetry FastAPI auto-instrumentation active.")
    except Exception as exc:
        logger.info(f"OpenTelemetry instrumentation skipped: {exc}")


def trace_span(span_name: str) -> Any:
    """
    Context manager or decorator helper for custom OpenTelemetry span tracing.
    """
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer("interviewsage_ai")
        return tracer.start_as_current_span(span_name)
    except Exception:
        # Fallback dummy context manager
        from contextlib import nullcontext
        return nullcontext()
