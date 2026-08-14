"""
Startup & Import Smoke Tests (Phase 1).
Verifies clean-clone import integrity, FastAPI initialization, critical settings, and workflow graph assembly.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.graph.workflow_master import build_master_workflow
from app.main import app


def test_application_import_and_creation():
    """Verify application object exists and is a valid FastAPI instance."""
    assert app is not None
    assert app.title == settings.app_name


def test_health_endpoint_response():
    """Verify health endpoint responds without throwing unhandled exceptions."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "subsystems" in data


def test_readiness_and_liveness_endpoints():
    """Verify readiness and liveness probes respond cleanly."""
    client = TestClient(app)
    readiness = client.get("/ready")
    assert readiness.status_code == 200
    assert readiness.json() == {"status": "ready"}

    liveness = client.get("/live")
    assert liveness.status_code == 200
    assert liveness.json() == {"status": "live"}


def test_critical_configuration_loaded():
    """Verify critical environment configuration parameters load cleanly."""
    assert settings.app_name is not None
    assert settings.database_url is not None
    assert settings.secret_key is not None


def test_master_workflow_graph_initialization():
    """Verify master LangGraph workflow graph compiles without error."""
    graph = build_master_workflow()
    assert graph is not None
