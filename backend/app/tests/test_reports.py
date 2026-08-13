"""
Comprehensive test suite for Candidate Report API endpoints and security contract (Step 4.2).
"""

import json
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Interview, InterviewReport, User, Resume, JobDescription
from app.services import AuthService


def _create_test_user(db: Session, email_suffix: str) -> tuple[User, str]:
    user_id = str(uuid.uuid4())
    email = f"candidate_{email_suffix}_{user_id[:8]}@example.com"
    user = User(
        id=user_id,
        email=email,
        full_name=f"Candidate {email_suffix}",
        password_hash=hash_password("Password123!"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = AuthService(db).create_user_token(user)
    return user, token


def _create_completed_interview_with_report(db: Session, user_id: str) -> tuple[Interview, InterviewReport]:
    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user_id,
        file_path="/uploads/resumes/sample.pdf",
        raw_text="Sample candidate resume content",
        parsed_skills=json.dumps(["Python", "FastAPI"]),
        parsed_experience=json.dumps([]),
    )
    jd = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user_id,
        target_role="Senior Python Engineer",
        raw_text="Sample job description content",
        required_skills=json.dumps(["Python"]),
    )
    db.add(resume)
    db.add(jd)
    db.commit()

    interview_id = str(uuid.uuid4())
    interview = Interview(
        id=interview_id,
        user_id=user_id,
        resume_id=resume.id,
        jd_id=jd.id,
        status="COMPLETED",
        overall_score=88,
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(interview)

    scorecard = [
        {"competency": "Technical Systems Architecture", "score": 90.0, "fullMark": 100},
        {"competency": "Problem Solving", "score": 86.0, "fullMark": 100},
    ]
    improvement_plan = [
        {
            "id": "imp-1",
            "topic": "System Concurrency",
            "description": "Improve knowledge of lock-free data structures.",
            "targetSkill": "Backend Architecture",
            "priority": "High",
        }
    ]
    transcript = [
        {
            "question": "What is database sharding?",
            "answer": "Horizontally partitioning data across servers.",
            "score": 90.0,
            "reasoning": "Accurate explanation.",
        }
    ]

    report = InterviewReport(
        id=str(uuid.uuid4()),
        interview_id=interview_id,
        competency_scorecard=json.dumps(scorecard),
        improvement_plan=json.dumps(improvement_plan),
        transcript_snapshot=json.dumps(transcript),
        generated_at=datetime.now(timezone.utc),
    )
    db.add(report)
    db.commit()
    db.refresh(interview)
    db.refresh(report)

    return interview, report


def test_get_report_completed_interview(client: TestClient, db_session: Session):
    """Owner successfully retrieves completed interview report."""
    user, token = _create_test_user(db_session, "owner")
    interview, report = _create_completed_interview_with_report(db_session, user.id)

    response = client.get(
        f"/api/v1/reports/{interview.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["interview_id"] == interview.id
    assert data["status"] == "COMPLETED"
    assert data["overall_score"] == 88.0
    assert len(data["competency_scorecard"]) == 2
    assert data["competency_scorecard"][0]["competency"] == "Technical Systems Architecture"
    assert len(data["improvement_plan"]) == 1
    assert len(data["transcript_snapshot"]) == 1


def test_get_report_incomplete_interview(client: TestClient, db_session: Session):
    """Attempting to fetch report for IN_PROGRESS interview returns 400 Bad Request."""
    user, token = _create_test_user(db_session, "in_progress")
    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user.id,
        file_path="/uploads/resumes/sample.pdf",
        raw_text="Sample candidate resume content",
        parsed_skills=json.dumps(["Python"]),
        parsed_experience=json.dumps([]),
    )
    jd = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        target_role="Backend Engineer",
        raw_text="Sample job description content",
        required_skills=json.dumps(["Python"]),
    )
    db_session.add(resume)
    db_session.add(jd)
    db_session.commit()

    interview_id = str(uuid.uuid4())
    interview = Interview(
        id=interview_id,
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        status="IN_PROGRESS",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(interview)
    db_session.commit()

    response = client.get(
        f"/api/v1/reports/{interview_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "IN_PROGRESS" in response.json()["detail"]


def test_get_report_forbidden_non_owner(client: TestClient, db_session: Session):
    """User B attempting to view User A's report gets 403 Forbidden."""
    user_a, _ = _create_test_user(db_session, "user_a")
    user_b, token_b = _create_test_user(db_session, "user_b")
    interview_a, _ = _create_completed_interview_with_report(db_session, user_a.id)

    response = client.get(
        f"/api/v1/reports/{interview_a.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]


def test_get_report_unauthenticated(client: TestClient, db_session: Session):
    """Unauthenticated GET request returns 401 or 403 (due to demo user fallback ownership failure)."""
    user, _ = _create_test_user(db_session, "unauth")
    interview, _ = _create_completed_interview_with_report(db_session, user.id)

    response = client.get(f"/api/v1/reports/{interview.id}")

    assert response.status_code in (401, 403)


def test_get_report_nonexistent_interview(client: TestClient, db_session: Session):
    """GET report for non-existent interview returns 404 Not Found."""
    _, token = _create_test_user(db_session, "not_found")
    random_id = str(uuid.uuid4())

    response = client.get(
        f"/api/v1/reports/{random_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_get_user_report_history(client: TestClient, db_session: Session):
    """Authenticated user receives only their own completed interview reports in history."""
    user_1, token_1 = _create_test_user(db_session, "history_1")
    user_2, _ = _create_test_user(db_session, "history_2")

    _create_completed_interview_with_report(db_session, user_1.id)
    _create_completed_interview_with_report(db_session, user_1.id)
    _create_completed_interview_with_report(db_session, user_2.id)

    response = client.get(
        "/api/v1/reports/user/history",
        headers={"Authorization": f"Bearer {token_1}"},
    )

    assert response.status_code == 200
    history = response.json()
    assert len(history) == 2
    for item in history:
        assert item["status"] == "COMPLETED"
        assert "overall_score" in item
        assert "generated_at" in item


def test_get_report_pdf_download(client: TestClient, db_session: Session):
    """Owner successfully downloads PDF report with application/pdf header."""
    user, token = _create_test_user(db_session, "pdf_owner")
    interview, _ = _create_completed_interview_with_report(db_session, user.id)

    response = client.get(
        f"/api/v1/reports/{interview.id}/pdf",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert len(response.content) > 0


def test_get_report_pdf_forbidden(client: TestClient, db_session: Session):
    """Non-owner attempting to download PDF receives 403 Forbidden."""
    user_a, _ = _create_test_user(db_session, "pdf_a")
    _, token_b = _create_test_user(db_session, "pdf_b")
    interview_a, _ = _create_completed_interview_with_report(db_session, user_a.id)

    response = client.get(
        f"/api/v1/reports/{interview_a.id}/pdf",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 403
