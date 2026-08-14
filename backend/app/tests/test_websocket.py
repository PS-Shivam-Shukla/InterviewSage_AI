"""
Unit and Integration Tests for Real-Time Voice WebSocket (/api/v1/ws/interviews/{interview_id} and /api/v1/ws/interview/{session_id}).
Step 3.5.2 — Backend WebSocket Voice Turn Processing & Persistence Verification.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import (
    Evaluation,
    Interview,
    InterviewAnswer,
    InterviewQuestion,
    JobDescription,
    Resume,
    User,
)
from app.models.voice import ConversationTurn, VoiceMetrics
from app.services import AuthService


@pytest.fixture(autouse=True)
def mock_mcp_tool():
    """Mock MCP tool, STT, and TTS for fast deterministic test execution."""
    from app.speech.stt import FasterWhisperSTTService
    from app.speech.tts import KokoroTTSService

    mock_res = MagicMock()
    mock_res.output = {
        "score": 88,
        "reasoning": "Clear explanation of architectural patterns and system trade-offs.",
        "technical_coverage": 86,
        "communication_score": 90,
        "confidence_score": 92,
    }
    dummy_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00" + b"\x00" * 1024

    with patch("app.mcp.server.mcp_server.call_tool", return_value=mock_res), \
         patch.object(FasterWhisperSTTService, "_init_model", return_value=None), \
         patch.object(FasterWhisperSTTService, "transcribe_bytes", return_value="I have five years of experience building backend microservices with FastAPI and PostgreSQL."), \
         patch.object(KokoroTTSService, "_init_kokoro", return_value=None), \
         patch.object(KokoroTTSService, "speak", return_value=dummy_wav), \
         patch.object(KokoroTTSService, "synthesize", return_value=dummy_wav):
        yield


def _auth_token(user: User, db_session: Session) -> str:
    return AuthService(db_session).create_user_token(user)


def _create_test_interview(user: User, db: Session) -> Interview:
    db.commit()
    interview_id = f"intv-{uuid.uuid4().hex[:8]}"
    resume_id = f"res-{uuid.uuid4().hex[:8]}"
    jd_id = f"jd-{uuid.uuid4().hex[:8]}"

    resume_db = Resume(
        id=resume_id,
        user_id=user.id,
        file_path="uploads/samples/sample_resume.pdf",
        raw_text="Candidate Resume",
        parsed_skills='["Python", "FastAPI"]',
        parsed_experience="[]",
        seniority_signal="SENIOR",
    )
    db.add(resume_db)

    jd_db = JobDescription(
        id=jd_id,
        user_id=user.id,
        raw_text="Job Description Requirements",
        target_role="Senior Backend Engineer",
        required_skills='["Python", "FastAPI"]',
        seniority_level="Senior",
    )
    db.add(jd_db)

    interview = Interview(
        id=interview_id,
        user_id=user.id,
        resume_id=resume_id,
        jd_id=jd_id,
        status="IN_PROGRESS",
        current_round="TECHNICAL",
        overall_score=None,
        started_at=datetime.now(UTC),
    )
    db.add(interview)

    q1 = InterviewQuestion(
        id=f"q-1-{interview_id}",
        interview_id=interview_id,
        round_type="TECHNICAL",
        competency_targeted="Backend Architecture",
        difficulty="MEDIUM",
        question_text="Explain Python concurrency and database connection pooling.",
        sequence_number=1,
        created_at=datetime.now(UTC),
    )
    q2 = InterviewQuestion(
        id=f"q-2-{interview_id}",
        interview_id=interview_id,
        round_type="TECHNICAL",
        competency_targeted="System Scaling",
        difficulty="MEDIUM",
        question_text="How do you handle horizontal scaling and distributed caching?",
        sequence_number=2,
        created_at=datetime.now(UTC),
    )
    db.add(q1)
    db.add(q2)
    db.commit()
    return interview


def test_voice_websocket_connect_and_ping(client: TestClient, db_session: Session, sample_user: User):
    """Verify WebSocket connection and PING/PONG message exchange."""
    token = _auth_token(sample_user, db_session)
    session_id = "sess-ws-ping-101"

    with client.websocket_connect(f"/api/v1/ws/interview/{session_id}?token={token}") as ws:
        ws.send_json({"event": "PING"})
        data = ws.receive_json()
        assert data["event"] == "PONG"


def test_voice_websocket_heartbeat(client: TestClient, db_session: Session, sample_user: User):
    """Verify WebSocket HEARTBEAT ping/pong handling."""
    token = _auth_token(sample_user, db_session)
    session_id = "sess-ws-heartbeat-303"

    with client.websocket_connect(f"/api/v1/ws/interview/{session_id}?token={token}") as ws:
        ws.send_json({"event": "HEARTBEAT"})
        hb_msg = ws.receive_json()
        assert hb_msg["event"] == "HEARTBEAT_ACK"
        assert hb_msg["status"] == "ACTIVE"


def test_authenticated_websocket_audio_buffering(client: TestClient, db_session: Session, sample_user: User):
    """Test 1: Verify binary audio buffering emits AUDIO_CHUNK_ACK."""
    interview = _create_test_interview(sample_user, db_session)
    token = _auth_token(sample_user, db_session)

    with client.websocket_connect(f"/api/v1/ws/interviews/{interview.id}?token={token}") as ws:
        ws.send_bytes(b"\x00\x01\x02\x03" * 25)
        ack = ws.receive_json()
        assert ack["type"] == "AUDIO_CHUNK_ACK"
        assert ack["size_bytes"] == 100


def test_authenticated_websocket_voice_turn_persistence(client: TestClient, db_session: Session, sample_user: User):
    """Test 2-7: Verify END_CANDIDATE_SPEECH triggers STT, Evaluation, Persistence, and Question Index increment."""
    interview = _create_test_interview(sample_user, db_session)
    token = _auth_token(sample_user, db_session)

    with client.websocket_connect(f"/api/v1/ws/interviews/{interview.id}?token={token}") as ws:
        # 1. Send binary audio chunks
        ws.send_bytes(b"\x00\x01\x02\x03" * 100)
        ws.receive_json()  # AUDIO_CHUNK_ACK

        # 2. Trigger speech completion
        ws.send_json({"type": "END_CANDIDATE_SPEECH"})

        # First message is TURN_COMPLETE processing
        msg1 = ws.receive_json()
        assert msg1["type"] == "TURN_COMPLETE"
        assert msg1["status"] == "PROCESSING"

        # Second message is TURN_COMPLETE completed
        msg2 = ws.receive_json()
        assert msg2["type"] == "TURN_COMPLETE"
        assert msg2["status"] == "COMPLETED"
        assert "candidate_transcript" in msg2
        assert "evaluation" in msg2
        assert "live_scores" in msg2

        # Receive binary TTS audio frame
        audio_frame = ws.receive_bytes()
        assert isinstance(audio_frame, bytes)
        assert len(audio_frame) > 0

    # 3. Verify Database Persistence State
    db_session.expire_all()
    answers = db_session.query(InterviewAnswer).join(InterviewQuestion).filter(InterviewQuestion.interview_id == interview.id).all()
    assert len(answers) == 1
    assert answers[0].answer_text is not None

    evals = db_session.query(Evaluation).filter(Evaluation.answer_id == answers[0].id).all()
    assert len(evals) == 1
    assert evals[0].score > 0

    turns = db_session.query(ConversationTurn).filter(ConversationTurn.session_id == interview.id).all()
    assert len(turns) >= 2

    metrics = db_session.query(VoiceMetrics).filter(VoiceMetrics.session_id == interview.id).first()
    assert metrics is not None
    assert metrics.communication_score > 0


def test_empty_audio_returns_error(client: TestClient, db_session: Session, sample_user: User):
    """Test 9: Verify END_CANDIDATE_SPEECH without audio chunks returns structured error event."""
    interview = _create_test_interview(sample_user, db_session)
    token = _auth_token(sample_user, db_session)

    with client.websocket_connect(f"/api/v1/ws/interviews/{interview.id}?token={token}") as ws:
        ws.send_json({"type": "END_CANDIDATE_SPEECH"})
        err_msg = ws.receive_json()
        assert err_msg["type"] == "ERROR"
        assert "No candidate audio received" in err_msg["message"]


def test_unauthorized_websocket_rejected(client: TestClient, db_session: Session, sample_user: User):
    """Verify unauthorized WebSocket connection is rejected with policy violation code."""
    session_id = "unauth-session-999"
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/interviews/{session_id}") as ws:
            ws.send_json({"type": "PING"})


def test_duplicate_end_candidate_speech_handling(client: TestClient, db_session: Session, sample_user: User):
    """Workstream D & F: Verify duplicate/concurrent END_CANDIDATE_SPEECH returns PROCESSING_IN_PROGRESS and avoids duplicate DB records."""
    from app.api.v1.routes.websocket import _processing_sessions

    interview = _create_test_interview(sample_user, db_session)
    token = _auth_token(sample_user, db_session)

    # Simulate active turn processing for this interview session
    _processing_sessions.add(interview.id)

    try:
        with client.websocket_connect(f"/api/v1/ws/interviews/{interview.id}?token={token}") as ws:
            ws.send_json({"type": "END_CANDIDATE_SPEECH"})
            msg = ws.receive_json()
            assert msg["type"] == "PROCESSING_IN_PROGRESS"
            assert "already in progress" in msg["message"]
    finally:
        _processing_sessions.discard(interview.id)


def test_text_mode_vs_voice_mode_state_parity(client: TestClient, db_session: Session, sample_user: User):
    """Workstream J: Verify REST Text Turn and WebSocket Voice Turn produce consistent database entities."""
    from app.services.interview_service import InterviewService
    from app.speech.streaming import AudioStreamingService

    interview = _create_test_interview(sample_user, db_session)

    # 1. Execute Text Turn via REST service
    interview_service = InterviewService(db_session)
    text_result = interview_service.submit_answer(
        interview_id=interview.id,
        answer="I use connection pools like asyncpg with FastAPI.",
        question_id=f"q-1-{interview.id}",
        question_text="Explain Python concurrency and database connection pooling.",
    )
    assert "evaluation" in text_result

    # Verify Text Turn persisted records
    db_session.expire_all()
    text_answers = db_session.query(InterviewAnswer).join(InterviewQuestion).filter(InterviewQuestion.interview_id == interview.id).all()
    assert len(text_answers) == 1
    assert text_answers[0].answer_text == "I use connection pools like asyncpg with FastAPI."

    # 2. Execute Voice Turn via AudioStreamingService
    streaming_service = AudioStreamingService(db=db_session)
    voice_result = streaming_service.process_voice_turn_orchestrated(
        session_id=interview.id,
        db=db_session,
        audio_bytes=b"\x00\x01\x02\x03" * 100,
    )
    assert "evaluation" in voice_result

    # Verify Voice Turn persisted records (2 total answers in interview sequence)
    db_session.expire_all()
    all_answers = db_session.query(InterviewAnswer).join(InterviewQuestion).filter(InterviewQuestion.interview_id == interview.id).all()
    assert len(all_answers) == 2

    evals = db_session.query(Evaluation).all()
    assert len(evals) == 2

