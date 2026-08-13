"""
Prometheus Metrics Subsystem for InterviewSage AI.
Exposes application counters, gauges, and histograms for production observability, AI Gateway tracing,
and Real-Time Voice Engine metrics.
"""

from __future__ import annotations

from typing import Any
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

# ── PROMETHEUS METRIC DEFINITIONS ────────────────────────────────

# Total interview creation and plan requests
INTERVIEW_REQUESTS_TOTAL = Counter(
    "interview_requests_total",
    "Total number of interview requests created or processed",
    ["status", "round_type"],
)

# Gauge for active interview sessions
ACTIVE_INTERVIEWS_GAUGE = Gauge(
    "active_interviews",
    "Number of currently active interview sessions",
)

# LangGraph node execution duration histogram
GRAPH_EXECUTION_SECONDS = Histogram(
    "graph_execution_seconds",
    "LangGraph node execution duration in seconds",
    ["node_name", "status"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# MCP tool invocation counter
MCP_TOOL_CALLS_TOTAL = Counter(
    "mcp_tool_calls_total",
    "Total number of MCP tool invocations",
    ["tool_name", "status"],
)

# LLM request counter
LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total number of LLM inference requests",
    ["model_name", "task_type"],
)

# LLM error counter
LLM_ERRORS_TOTAL = Counter(
    "llm_errors_total",
    "Total number of LLM request failures",
    ["model_name"],
)

# Database query duration histogram
DATABASE_QUERY_SECONDS = Histogram(
    "database_query_seconds",
    "Database query execution duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# ── SPRINT 9 AI GATEWAY SPECIFIC METRICS ─────────────────────────

# LLM request latency histogram
LLM_LATENCY_SECONDS = Histogram(
    "llm_latency_seconds",
    "LLM request latency in seconds",
    ["provider", "model_name"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

# LLM retry attempts counter
LLM_RETRY_TOTAL = Counter(
    "llm_retry_total",
    "Total number of LLM request retry attempts",
    ["provider"],
)

# LLM unrecoverable failures counter
LLM_FAILURES_TOTAL = Counter(
    "llm_failures_total",
    "Total number of unrecoverable LLM failures",
    ["provider"],
)

# LLM token consumption counter
LLM_TOKENS_TOTAL = Counter(
    "llm_tokens_total",
    "Total number of LLM tokens consumed",
    ["token_type", "provider", "model_name"],
)

# LLM estimated cost counter (USD)
LLM_COST_TOTAL = Counter(
    "llm_cost_total",
    "Total estimated LLM cost in USD",
    ["provider", "model_name"],
)

# Prompt version usage counter
PROMPT_VERSION_USAGE_TOTAL = Counter(
    "prompt_version_usage_total",
    "Total number of prompt template executions by version",
    ["prompt_key", "version"],
)

# ── SPRINT 13 REAL-TIME VOICE ENGINE METRICS ─────────────────────

VOICE_REQUESTS_TOTAL = Counter(
    "voice_requests_total",
    "Total number of voice WebSocket requests",
)

ACTIVE_VOICE_SESSIONS = Gauge(
    "active_voice_sessions",
    "Number of currently active voice sessions",
)

VOICE_LATENCY_SECONDS = Histogram(
    "voice_latency_seconds",
    "Total end-to-end voice processing latency in seconds",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

TRANSCRIPTION_DURATION = Histogram(
    "transcription_duration_seconds",
    "STT transcription duration in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

TTS_DURATION = Histogram(
    "tts_duration_seconds",
    "TTS synthesis duration in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

STREAM_DISCONNECTS = Counter(
    "stream_disconnects_total",
    "Total voice WebSocket disconnects",
)


def get_metrics_response() -> Response:
    """
    Generate Prometheus metrics HTTP response payload.
    """
    metrics_data = generate_latest()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)
