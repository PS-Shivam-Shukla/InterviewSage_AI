"""
Unit and Integration Tests for Candidate Voice Summary & GET /api/v1/analytics/voice (Step 4.4).
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User, LiveSession, VoiceMetrics
from app.services import AuthService


def _create_test_user(db: Session, email_suffix: str) -> tuple[User, str]:
    user_id = str(uuid.uuid4())
    email = f"candidate_voice_{email_suffix}_{user_id[:8]}@example.com"
    user = User(
        id=user_id,
        email=email,
        full_name=f"Candidate Voice {email_suffix}",
        password_hash=hash_password("Password123!"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = AuthService(db).create_user_token(user)
    return user, token


def test_candidate_voice_analytics_aggregation(client: TestClient, db_session: Session):
    """Candidate with multiple voice sessions receives aggregated voice metrics."""
    user, token = _create_test_user(db_session, "user_multi")

    # Create session 1
    session_1_id = str(uuid.uuid4())
    vm1 = VoiceMetrics(
        id=str(uuid.uuid4()),
        session_id=session_1_id,
        candidate_id=user.id,
        avg_speaking_speed_wpm=140.0,
        total_speaking_time_seconds=120.0,
        total_silence_duration_seconds=5.0,
        answer_latency_avg_seconds=1.2,
        total_words_spoken=280,
        technical_score=85.0,
        communication_score=90.0,
        confidence_estimate=88.0,
    )
    db_session.add(vm1)

    # Create session 2
    session_2_id = str(uuid.uuid4())
    vm2 = VoiceMetrics(
        id=str(uuid.uuid4()),
        session_id=session_2_id,
        candidate_id=user.id,
        avg_speaking_speed_wpm=150.0,
        total_speaking_time_seconds=180.0,
        total_silence_duration_seconds=10.0,
        answer_latency_avg_seconds=1.6,
        total_words_spoken=450,
        technical_score=89.0,
        communication_score=92.0,
        confidence_estimate=90.0,
    )
    db_session.add(vm2)
    db_session.commit()

    response = client.get(
        "/api/v1/analytics/voice",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    voice_data = response.json()["voice"]
    assert voice_data["has_voice_data"] is True
    assert voice_data["voice_sessions_count"] == 2
    assert voice_data["avg_speaking_speed_wpm"] == 145.0
    assert voice_data["total_speaking_time_seconds"] == 300.0
    assert voice_data["total_silence_duration_seconds"] == 15.0
    assert voice_data["avg_answer_latency_seconds"] == 1.4
    assert voice_data["total_words_spoken"] == 730
    assert voice_data["avg_communication_score"] == 91.0
    assert voice_data["avg_technical_score"] == 87.0
    assert voice_data["avg_confidence_estimate"] == 89.0


def test_candidate_no_voice_data(client: TestClient, db_session: Session):
    """Candidate with no voice sessions receives has_voice_data = False."""
    _, token = _create_test_user(db_session, "user_empty")

    response = client.get(
        "/api/v1/analytics/voice",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    voice_data = response.json()["voice"]
    assert voice_data["has_voice_data"] is False
    assert voice_data["voice_sessions_count"] == 0
    assert "avg_speaking_speed_wpm" not in voice_data


def test_candidate_voice_metrics_isolation(client: TestClient, db_session: Session):
    """Candidate A cannot receive Candidate B's voice metrics."""
    user_a, _ = _create_test_user(db_session, "user_a")
    _, token_b = _create_test_user(db_session, "user_b")

    # Add voice metric for Candidate A
    vm_a = VoiceMetrics(
        id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        candidate_id=user_a.id,
        avg_speaking_speed_wpm=135.0,
        total_speaking_time_seconds=90.0,
        total_silence_duration_seconds=2.0,
        answer_latency_avg_seconds=1.0,
        total_words_spoken=200,
        technical_score=80.0,
        communication_score=80.0,
        confidence_estimate=80.0,
    )
    db_session.add(vm_a)
    db_session.commit()

    # Candidate B requests voice analytics
    response = client.get(
        "/api/v1/analytics/voice",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 200
    voice_data = response.json()["voice"]
    assert voice_data["has_voice_data"] is False
    assert voice_data["voice_sessions_count"] == 0


def test_existing_analytics_endpoints_intact(client: TestClient, db_session: Session):
    """Verify GET /analytics/summary, /trends, and /competencies endpoints continue working cleanly."""
    _, token = _create_test_user(db_session, "user_endpoints")
    headers = {"Authorization": f"Bearer {token}"}

    res_sum = client.get("/api/v1/analytics/summary", headers=headers)
    assert res_sum.status_code == 200
    assert "summary" in res_sum.json()

    res_trends = client.get("/api/v1/analytics/trends", headers=headers)
    assert res_trends.status_code == 200
    assert "trends" in res_trends.json()

    res_comp = client.get("/api/v1/analytics/competencies", headers=headers)
    assert res_comp.status_code == 200
    assert "competencies" in res_comp.json()
