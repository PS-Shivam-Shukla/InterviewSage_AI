"""
Unit and Integration Tests for AI Career Intelligence API Routes (/api/v1/career/*).
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Interview, User
from app.services import AuthService


def _auth_headers(user: User, db_session: Session) -> dict[str, str]:
    token = AuthService(db_session).create_user_token(user)
    return {"Authorization": f"Bearer {token}"}


def test_get_hiring_prediction_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify GET /api/v1/career/hiring-prediction/{candidate_id}."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/career/hiring-prediction/{sample_user.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == sample_user.id
    assert "hire_probability" in data
    assert "outcome" in data


def test_get_benchmark_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify GET /api/v1/career/benchmark/{candidate_id}."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/career/benchmark/{sample_user.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "overall_percentile" in data
    assert len(data["categories"]) >= 3


def test_get_company_profile_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify GET /api/v1/career/company/{company}."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get("/api/v1/career/company/Amazon", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["company_name"] == "Amazon"
    assert "behavioral_weight" in data


def test_adaptive_session_routes(
    client: TestClient, db_session: Session, sample_user: User, sample_interview: Interview
):
    """Verify POST /api/v1/career/adaptive/start and /next-question."""
    headers = _auth_headers(sample_user, db_session)
    start_res = client.post(
        "/api/v1/career/adaptive/start",
        json={
            "interview_id": sample_interview.id,
            "candidate_id": sample_user.id,
            "initial_difficulty": 5.0,
        },
        headers=headers,
    )
    assert start_res.status_code == 200
    start_data = start_res.json()
    sess_id = start_data["session_id"]

    next_res = client.post(
        "/api/v1/career/adaptive/next-question",
        json={"session_id": sess_id, "performance_score": 88.0, "response_latency_seconds": 15.0},
        headers=headers,
    )
    assert next_res.status_code == 200
    next_data = next_res.json()
    assert next_data["new_difficulty"] > 5.0


def test_roadmap_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify GET /api/v1/career/roadmap/{candidate_id}."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/career/roadmap/{sample_user.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "daily_plan" in data


def test_replay_route(
    client: TestClient, db_session: Session, sample_user: User, sample_interview: Interview
):
    """Verify GET /api/v1/career/replay/{interview_id}."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/career/replay/{sample_interview.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "annotations" in data


def test_skill_gap_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify GET /api/v1/career/skill-gap/{candidate_id}."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/career/skill-gap/{sample_user.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "gaps" in data


def test_recruiter_insights_route(
    client: TestClient, db_session: Session, sample_user: User, sample_interview: Interview
):
    """Verify GET /api/v1/career/recruiter-insights/{interview_id}."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/career/recruiter-insights/{sample_interview.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "primary_rejection_factors" in data
