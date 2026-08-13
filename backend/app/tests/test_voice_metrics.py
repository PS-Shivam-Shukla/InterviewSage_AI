"""
Unit and Integration Tests for VoiceAnalyticsService & GET /api/v1/voice/{session_id}.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Interview
from app.services import AuthService
from app.speech.analytics import VoiceAnalyticsService
from app.transcript.service import TranscriptService


def _auth_headers(user: User, db_session: Session) -> dict[str, str]:
    token = AuthService(db_session).create_user_token(user)
    return {"Authorization": f"Bearer {token}"}


def test_voice_analytics_deterministic_metrics(db_session: Session, sample_user: User, sample_interview: Interview):
    """Verify deterministic VoiceAnalyticsService WPM, silence, answer latency, and scores calculation."""
    transcript_service = TranscriptService(db_session)
    session_id = "sess-analytics-101"

    transcript_service.repo.get_or_create_live_session(
        session_id=session_id, interview_id=sample_interview.id, candidate_id=sample_user.id
    )

    transcript_service.record_turn(
        session_id, "AI_AGENT", "What is your experience with Kubernetes operators?", agent_name="TechnicalInterviewAgent"
    )
    transcript_service.record_turn(
        session_id, "CANDIDATE", "I have deployed custom Kubernetes operators using Python and Kopf framework.", duration_seconds=5.0
    )

    analytics = VoiceAnalyticsService(db_session)
    metrics = analytics.compute_session_voice_metrics(session_id)

    assert metrics.session_id == session_id
    assert metrics.total_words_spoken > 0
    assert metrics.avg_speaking_speed_wpm > 0.0
    assert metrics.technical_score is None
    assert metrics.communication_score >= 40.0
    assert metrics.confidence_estimate >= 40.0


def test_get_voice_metrics_route(client: TestClient, db_session: Session, sample_user: User, sample_interview: Interview):
    """Verify GET /api/v1/voice/{session_id} API endpoint."""
    transcript_service = TranscriptService(db_session)
    session_id = "sess-route-voice-202"

    transcript_service.repo.get_or_create_live_session(
        session_id=session_id, interview_id=sample_interview.id, candidate_id=sample_user.id
    )
    transcript_service.record_turn(session_id, "CANDIDATE", "Testing voice metrics route.")

    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/voice/{session_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["session_id"] == session_id
    assert "avg_speaking_speed_wpm" in data
    assert "technical_score" in data
