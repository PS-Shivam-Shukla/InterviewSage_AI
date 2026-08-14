"""
Unit and Integration Tests for Transcript Engine & Download Routes (/api/v1/transcripts/*).
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Interview, User
from app.services import AuthService
from app.transcript.service import TranscriptService


def _auth_headers(user: User, db_session: Session) -> dict[str, str]:
    token = AuthService(db_session).create_user_token(user)
    return {"Authorization": f"Bearer {token}"}


def test_transcript_service_record_and_compile(
    db_session: Session, sample_user: User, sample_interview: Interview
):
    """Verify TranscriptService records turns and compiles full transcript export."""
    service = TranscriptService(db_session)
    session_id = "sess-trans-101"

    service.record_turn(
        session_id,
        "CANDIDATE",
        "I built an event-driven architecture using Kafka.",
        duration_seconds=4.5,
    )
    service.record_turn(
        session_id,
        "AI_AGENT",
        "How did you ensure message ordering across partitions?",
        duration_seconds=3.0,
    )

    export = service.compile_full_transcript(
        session_id=session_id, interview_id=sample_interview.id
    )
    assert export.interview_id == sample_interview.id
    assert export.turn_count == 2
    assert "Kafka" in export.full_text


def test_get_transcript_route(
    client: TestClient, db_session: Session, sample_user: User, sample_interview: Interview
):
    """Verify GET /api/v1/transcripts/{interview_id} route."""
    service = TranscriptService(db_session)
    session_id = "sess-route-202"
    service.record_turn(session_id, "CANDIDATE", "I optimized PostgreSQL query execution plans.")
    service.compile_full_transcript(session_id=session_id, interview_id=sample_interview.id)

    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/transcripts/{sample_interview.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["interview_id"] == sample_interview.id
    assert "PostgreSQL" in data["full_text"]


def test_download_transcript_route(
    client: TestClient, db_session: Session, sample_user: User, sample_interview: Interview
):
    """Verify GET /api/v1/transcripts/{interview_id}/download text download route."""
    service = TranscriptService(db_session)
    session_id = "sess-dl-303"
    service.record_turn(session_id, "CANDIDATE", "I implemented Redis distributed caching.")
    service.compile_full_transcript(session_id=session_id, interview_id=sample_interview.id)

    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/transcripts/{sample_interview.id}/download", headers=headers)
    assert res.status_code == 200
    assert "text/plain" in res.headers["content-type"]
    assert "Content-Disposition" in res.headers
    assert "Redis" in res.text
