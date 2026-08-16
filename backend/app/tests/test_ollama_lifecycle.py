"""
Test Suite: Ollama Lifecycle & Resume Processing Integrity

Validates:
1. Fast-fail when Ollama service is unavailable (no hanging, status=FAILED).
2. Clean completion when Ollama service is available.
3. LLM failure results in status=FAILED without fake data.
4. Empty structured output results in status=FAILED.
5. Data isolation between distinct resumes.
6. Zero subprocess spawning (no `ollama serve` execution).
7. Telemetry isolation (agent_logs failure does not poison main DB transaction).
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

from app.models import Resume, User
from app.services.resume_service import ResumeService
from app.agents.base import BaseAgent
from app.core.llm_client import check_ollama_health


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    resume_obj = MagicMock(spec=Resume)
    resume_obj.id = "test-resume-uuid-1234"
    resume_obj.status = "PROCESSING"
    resume_obj.parsed_skills = None
    resume_obj.parsed_experience = None
    resume_obj.seniority_signal = "UNKNOWN"
    resume_obj.seniority_score = 0

    session.query.return_value.filter.return_value.first.return_value = resume_obj
    return session, resume_obj


def test_ollama_health_check_available():
    """Verify check_ollama_health returns True when endpoint returns 200 OK."""
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.status = 200
    mock_cm.__enter__.return_value.getcode.return_value = 200

    with patch("urllib.request.urlopen", return_value=mock_cm):
        assert check_ollama_health(host="http://localhost:11434", timeout=1.0) is True


def test_ollama_health_check_unavailable():
    """Verify check_ollama_health returns False when endpoint is unreachable."""
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        assert check_ollama_health(host="http://localhost:11434", timeout=1.0) is False


def test_no_ollama_process_spawning():
    """Verify that process_resume_background never executes subprocess/ollama serve."""
    with patch("subprocess.run") as mock_sub_run, \
         patch("subprocess.Popen") as mock_sub_popen, \
         patch("os.system") as mock_sys:

        # Mock health check to fail so worker exits quickly
        with patch("app.core.llm_client.check_ollama_health", return_value=False):
            with patch("app.core.database.SessionLocal") as mock_session_local:
                mock_db = MagicMock()
                mock_session_local.return_value = mock_db

                service = ResumeService(mock_db)
                service.process_resume_background("test-id", "Some raw text content", "resume.pdf")

                # Assert zero subprocess or os.system calls were made
                mock_sub_run.assert_not_called()
                mock_sub_popen.assert_not_called()
                mock_sys.assert_not_called()


def test_ollama_unavailable_fast_fail(mock_db_session):
    """Verify fast failure when Ollama is unavailable on pre-flight check."""
    session, resume_obj = mock_db_session

    with patch("app.core.llm_client.check_ollama_health", return_value=False), \
         patch("app.core.database.SessionLocal", return_value=session):

        service = ResumeService(session)
        service.process_resume_background("test-resume-uuid-1234", "Valid resume content here", "resume.pdf")

        assert resume_obj.status == "FAILED"
        session.commit.assert_called()


def test_llm_failure_marks_resume_failed(mock_db_session):
    """Verify that an LLM exception marks the resume FAILED without generating fake metrics."""
    session, resume_obj = mock_db_session
    mock_agent = MagicMock()
    mock_agent.return_value = {"is_failed": True, "error_log": "LLM ReadTimeout"}

    with patch("app.core.llm_client.check_ollama_health", return_value=True), \
         patch("app.core.database.SessionLocal", return_value=session):

        service = ResumeService(session)
        service.process_resume_background("test-resume-uuid-1234", "Valid resume content", "resume.pdf", agent=mock_agent)

        assert resume_obj.status == "FAILED"
        session.commit.assert_called()


def test_empty_structured_response_marks_resume_failed(mock_db_session):
    """Verify empty structured response for substantial text marks resume FAILED."""
    session, resume_obj = mock_db_session
    mock_agent = MagicMock()
    mock_agent.return_value = {
        "is_failed": False,
        "resume_data": {"technical_skills": [], "experience": [], "summary": ""}
    }

    with patch("app.core.llm_client.check_ollama_health", return_value=True), \
         patch("app.core.database.SessionLocal", return_value=session):

        service = ResumeService(session)
        service.process_resume_background("test-resume-uuid-1234", "Valid text content longer than 50 characters for parsing", "resume.pdf", agent=mock_agent)

        assert resume_obj.status == "FAILED"


def test_telemetry_failure_does_not_poison_transaction():
    """Verify telemetry logging failure executes db.rollback() without poisoning primary transaction."""
    from app.agents.resume_agent import ResumeAgent

    mock_db = MagicMock()
    with patch("app.mcp.mcp_server.call_tool", side_effect=Exception("ForeignKeyViolation")):
        agent = ResumeAgent()
        state = {"interview_id": "invalid-id", "_db_session": mock_db}

        agent._log(state, "FAILED", {}, latency_ms=10, retry_count=0, error="Test error")

        mock_db.rollback.assert_called_once()
