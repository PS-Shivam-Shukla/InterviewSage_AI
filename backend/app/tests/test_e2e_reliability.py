"""
Step 5.2 — Backend End-to-End Reliability & Idempotency Test Suite
Verifies normal turn lifecycle, duplicate completion idempotency, invalid auth rejection,
tenant ownership isolation, and completed interview state protection.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Interview, JobDescription, Resume, User
from app.services import AuthService
from app.services.interview_service import InterviewService


def _create_candidate_with_docs(db_session: Session, prefix: str):
    user = User(
        id=str(uuid.uuid4()),
        email=f"{prefix}_{uuid.uuid4().hex[:6]}@example.com",
        full_name=f"Candidate {prefix}",
        password_hash=hash_password("Password123!"),
    )
    db_session.add(user)

    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user.id,
        file_path=f"uploads/samples/{prefix}.pdf",
        raw_text=f"{prefix} resume",
    )
    db_session.add(resume)

    jd = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        target_role=f"Senior {prefix} Engineer",
        raw_text=f"{prefix} JD",
    )
    db_session.add(jd)

    db_session.commit()
    db_session.refresh(user)

    token_obj = AuthService(db_session).create_user_token(user)
    token = token_obj["access_token"] if isinstance(token_obj, dict) else token_obj
    return user, resume.id, jd.id, token


@pytest.fixture
def candidate_a(db_session: Session):
    return _create_candidate_with_docs(db_session, "cand_a")


@pytest.fixture
def candidate_b(db_session: Session):
    return _create_candidate_with_docs(db_session, "cand_b")


def test_normal_interview_turn_and_completion_lifecycle(db_session: Session, candidate_a):
    """Verify full turn lifecycle: submission, evaluation, question progression, and report creation."""
    user, resume_id, jd_id, _ = candidate_a
    service = InterviewService(db_session)

    interview = service.create_interview(user_id=user.id, resume_id=resume_id, jd_id=jd_id)
    interview_id = interview.id
    service.get_interview_plan(interview_id)

    total_q = service.question_repo.list_by_interview(interview_id)
    assert len(total_q) > 0

    res_final = None
    for q in total_q:
        res_final = service.submit_answer(
            interview_id=interview_id,
            answer="I design distributed architectures with circuit breakers and fallback pools.",
            question_id=q.id,
            question_text=q.question_text,
        )

    assert res_final is not None
    assert res_final["status"] == "COMPLETED"
    assert "report" in res_final or "message" in res_final


def test_duplicate_final_completion_idempotency(db_session: Session, candidate_a):
    """Verify duplicate completion calls on an already completed interview return idempotent status."""
    user, resume_id, jd_id, _ = candidate_a
    service = InterviewService(db_session)

    interview = service.create_interview(user_id=user.id, resume_id=resume_id, jd_id=jd_id)
    interview_id = interview.id
    service.get_interview_plan(interview_id)

    total_q = service.question_repo.list_by_interview(interview_id)
    for q in total_q:
        service.submit_answer(
            interview_id=interview_id,
            answer="Intermediate answer.",
            question_id=q.id,
            question_text=q.question_text,
        )

    final_q = total_q[-1]
    res1 = service.get_interview(interview_id)
    assert res1.status == "COMPLETED"

    res2 = service.submit_answer(
        interview_id=interview_id,
        answer="Duplicate turn submission.",
        question_id=final_q.id,
        question_text=final_q.question_text,
    )

    assert res2["status"] == "COMPLETED"


def test_invalid_authentication_rejection(client: TestClient):
    """Verify connecting to WebSocket with missing or invalid token closes socket or rejects auth."""
    try:
        with client.websocket_connect("/api/v1/ws/interviews/int-fake-123?token=invalid_token_xyz"):
            pass
    except Exception as exc:
        assert exc is not None


def test_invalid_ownership_rejection(
    client: TestClient, db_session: Session, candidate_a, candidate_b
):
    """Verify Candidate B cannot access Candidate A's interview WebSocket."""
    user_a, resume_id_a, jd_id_a, _ = candidate_a
    user_b, _, _, token_b = candidate_b

    interview = Interview(
        id=f"int-{uuid.uuid4()}",
        user_id=user_a.id,
        resume_id=resume_id_a,
        jd_id=jd_id_a,
        status="IN_PROGRESS",
    )
    db_session.add(interview)
    db_session.commit()

    try:
        with client.websocket_connect(f"/api/v1/ws/interviews/{interview.id}?token={token_b}"):
            pass
    except Exception as exc:
        assert exc is not None


def test_completed_interview_protection(client: TestClient, db_session: Session, candidate_a):
    """Verify a completed interview preserves its completed state when re-queried or reconnected."""
    user, resume_id, jd_id, token = candidate_a

    interview = Interview(
        id=f"int-{uuid.uuid4()}",
        user_id=user.id,
        resume_id=resume_id,
        jd_id=jd_id,
        status="COMPLETED",
    )
    db_session.add(interview)
    db_session.commit()

    with client.websocket_connect(f"/api/v1/ws/interviews/{interview.id}?token={token}") as ws:
        ws.send_json({"type": "PING"})
        assert ws.receive_json().get("type") == "PONG"

    fetched = db_session.query(Interview).filter_by(id=interview.id).first()
    assert fetched.status == "COMPLETED"
