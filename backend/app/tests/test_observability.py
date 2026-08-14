"""
Phase 3 - Sprint 7: Production Observability & Monitoring Test Suite.
Verifies Request Correlation IDs, Structured JSON Logging, Prometheus Metrics, and Health Probes.
"""

import json
import logging

from fastapi.testclient import TestClient

from app.core.logging import StructuredFormatter
from app.core.metrics import GRAPH_EXECUTION_SECONDS, INTERVIEW_REQUESTS_TOTAL
from app.core.request_context import set_request_context
from app.main import app

client = TestClient(app)


def test_request_id_middleware_injects_header():
    """Verify X-Request-ID is generated and returned in response headers."""
    response = client.get("/live")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req-")


def test_custom_request_id_propagates():
    """Verify incoming X-Request-ID header is preserved and returned."""
    custom_id = "test-correlation-id-999"
    response = client.get("/ready", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_health_readiness_liveness_probes():
    """Verify GET /health, GET /ready, and GET /live endpoints."""
    # Health Probe
    res_health = client.get("/health")
    assert res_health.status_code in [200, 503]
    health_json = res_health.json()
    assert "status" in health_json
    assert "subsystems" in health_json

    # Readiness Probe
    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json() == {"status": "ready"}

    # Liveness Probe
    res_live = client.get("/live")
    assert res_live.status_code == 200
    assert res_live.json() == {"status": "live"}


def test_prometheus_metrics_endpoint():
    """Verify GET /metrics exposes Prometheus metric metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert "interview_requests_total" in body or "graph_execution_seconds" in body or "python_gc_" in body


def test_structured_json_logging_format():
    """Verify StructuredFormatter outputs valid JSON with required observability fields."""
    formatter = StructuredFormatter()
    set_request_context(request_id="req-unit-test", user_id="usr-test", interview_id="int-test")

    logger = logging.getLogger("test_logger")
    record = logger.makeRecord(
        name="test_logger",
        level=logging.INFO,
        fn="test_observability.py",
        lno=42,
        msg="Observability structured log test",
        args=(),
        exc_info=None,
    )
    record.duration_ms = 14.5

    formatted_json_str = formatter.format(record)
    log_dict = json.loads(formatted_json_str)

    assert log_dict["level"] == "INFO"
    assert log_dict["logger"] == "test_logger"
    assert log_dict["message"] == "Observability structured log test"
    assert log_dict["service"] == "InterviewSageAI"
    assert log_dict["request_id"] == "req-unit-test"
    assert log_dict["user_id"] == "usr-test"
    assert log_dict["interview_id"] == "int-test"
    assert log_dict["duration_ms"] == 14.5
    assert "timestamp" in log_dict


def test_metrics_counter_and_histogram_recording():
    """Verify metrics counters and histograms record observations without throwing exceptions."""
    INTERVIEW_REQUESTS_TOTAL.labels(status="success", round_type="TECHNICAL").inc()
    GRAPH_EXECUTION_SECONDS.labels(node_name="test_node", status="success").observe(0.045)

    response = client.get("/metrics")
    assert response.status_code == 200
    assert "interview_requests_total" in response.text
