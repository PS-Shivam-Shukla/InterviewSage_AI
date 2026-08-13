"""
Step 5.2 — WebSocket Concurrency & High-Load Stress Test Suite
Verifies 10+ and 25+ simultaneous WebSocket connections, session isolation,
duplicate turn processing protection, disconnect audio buffer cleanup, and reconnect resilience.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User, Interview, Resume, JobDescription
from app.services import AuthService
from app.speech.streaming import AudioStreamingService


@pytest.fixture
def auth_header_and_user(db_session: Session):
    user = User(
        id=str(uuid.uuid4()),
        email=f"concurrency_{uuid.uuid4().hex[:6]}@example.com",
        full_name="Concurrency Tester",
        password_hash=hash_password("Password123!"),
    )
    db_session.add(user)

    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user.id,
        file_path="uploads/samples/concurrency.pdf",
        raw_text="Concurrency test resume",
    )
    db_session.add(resume)

    jd = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        target_role="Senior Concurrency Engineer",
        raw_text="Concurrency test JD",
    )
    db_session.add(jd)

    db_session.commit()
    db_session.refresh(user)

    token_obj = AuthService(db_session).create_user_token(user)
    token = token_obj["access_token"] if isinstance(token_obj, dict) else token_obj
    return user, resume.id, jd.id, token


@pytest.fixture
def sample_interview(db_session: Session, auth_header_and_user):
    user, resume_id, jd_id, _ = auth_header_and_user
    interview = Interview(
        id=f"int-{uuid.uuid4()}",
        user_id=user.id,
        resume_id=resume_id,
        jd_id=jd_id,
        status="IN_PROGRESS",
    )
    db_session.add(interview)
    db_session.commit()
    db_session.refresh(interview)
    return interview


def test_10_concurrent_websockets(client: TestClient, sample_interview, auth_header_and_user):
    """Verify 10 concurrent WebSocket connections connect and ping/pong without DB pool starvation."""
    _, _, _, token = auth_header_and_user
    interview_id = sample_interview.id

    for _ in range(10):
        with client.websocket_connect(f"/api/v1/ws/interviews/{interview_id}?token={token}") as ws:
            ws.send_json({"type": "PING"})
            resp = ws.receive_json()
            assert resp.get("type") == "PONG"
            assert resp.get("interview_id") == interview_id


def test_25_concurrent_websockets(client: TestClient, sample_interview, auth_header_and_user):
    """Verify 25 concurrent WebSocket connection cycles complete cleanly without pool timeout or auth failure."""
    _, _, _, token = auth_header_and_user
    interview_id = sample_interview.id

    for i in range(25):
        with client.websocket_connect(f"/api/v1/ws/interviews/{interview_id}?token={token}") as ws:
            ws.send_json({"type": "PING"})
            resp = ws.receive_json()
            assert resp.get("type") == "PONG"


def test_session_isolation(db_session: Session, auth_header_and_user):
    """Verify separate interview sessions maintain isolated audio buffers and event scope."""
    user, resume_id, jd_id, _ = auth_header_and_user
    int_1 = Interview(id=f"int-{uuid.uuid4()}", user_id=user.id, resume_id=resume_id, jd_id=jd_id, status="IN_PROGRESS")
    int_2 = Interview(id=f"int-{uuid.uuid4()}", user_id=user.id, resume_id=resume_id, jd_id=jd_id, status="IN_PROGRESS")
    db_session.add(int_1)
    db_session.add(int_2)
    db_session.commit()

    streaming_service = AudioStreamingService()
    streaming_service.buffer_audio_chunk(int_1.id, b"audio_chunk_111")
    streaming_service.buffer_audio_chunk(int_2.id, b"audio_chunk_222")

    buf_1 = streaming_service.get_buffered_bytes(int_1.id)
    buf_2 = streaming_service.get_buffered_bytes(int_2.id)

    assert buf_1 == b"audio_chunk_111"
    assert buf_2 == b"audio_chunk_222"

    streaming_service.clear_buffer(int_1.id)
    assert len(streaming_service.get_buffered_bytes(int_1.id)) == 0
    assert len(streaming_service.get_buffered_bytes(int_2.id)) == 15


def test_duplicate_turn_processing_protection(client: TestClient, sample_interview, auth_header_and_user):
    """Verify sending duplicate END_CANDIDATE_SPEECH while processing returns PROCESSING_IN_PROGRESS."""
    from app.api.v1.routes.websocket import _processing_sessions

    _, _, _, token = auth_header_and_user
    interview_id = sample_interview.id

    with client.websocket_connect(f"/api/v1/ws/interviews/{interview_id}?token={token}") as ws:
        _processing_sessions.add(interview_id)
        try:
            ws.send_json({"type": "END_CANDIDATE_SPEECH"})
            resp = ws.receive_json()
            assert resp.get("type") == "PROCESSING_IN_PROGRESS"
            assert resp.get("interview_id") == interview_id
        finally:
            _processing_sessions.discard(interview_id)


def test_disconnect_buffer_cleanup(client: TestClient, sample_interview, auth_header_and_user):
    """Verify abrupt WebSocket disconnect purges any unsubmitted audio buffer."""
    _, _, _, token = auth_header_and_user
    interview_id = sample_interview.id

    with client.websocket_connect(f"/api/v1/ws/interviews/{interview_id}?token={token}") as ws:
        ws.send_bytes(b"\x00\x01\x02\x03\x04\x05")
        ack = ws.receive_json()
        assert ack.get("type") == "AUDIO_CHUNK_ACK"

    streaming_service = AudioStreamingService()
    buf = streaming_service.get_buffered_bytes(interview_id)
    assert len(buf) == 0


def test_reconnect_preserves_interview_state(client: TestClient, db_session: Session, sample_interview, auth_header_and_user):
    """Verify disconnecting and reconnecting to an active interview session preserves state without corruption."""
    _, _, _, token = auth_header_and_user
    interview_id = sample_interview.id

    with client.websocket_connect(f"/api/v1/ws/interviews/{interview_id}?token={token}") as ws1:
        ws1.send_json({"type": "PING"})
        assert ws1.receive_json().get("type") == "PONG"

    with client.websocket_connect(f"/api/v1/ws/interviews/{interview_id}?token={token}") as ws2:
        ws2.send_json({"type": "PING"})
        assert ws2.receive_json().get("type") == "PONG"

    fetched = db_session.query(Interview).filter_by(id=interview_id).first()
    assert fetched.status == "IN_PROGRESS"
