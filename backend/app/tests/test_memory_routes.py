"""
Integration Tests for Candidate Memory API Routes (/api/v1/memory/*).
Validates ownership authorization, CRUD, skill progression, recommendations, and memory compression.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from app.services import AuthService


def _auth_headers(user: User, db_session: Session) -> dict[str, str]:
    token = AuthService(db_session).create_user_token(user)
    return {"Authorization": f"Bearer {token}"}


def test_get_candidate_memory_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify GET /api/v1/memory/{candidate_id}."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/memory/{sample_user.id}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == sample_user.id
    assert "skills" in data


def test_save_candidate_memory_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify POST /api/v1/memory/{candidate_id}."""
    headers = _auth_headers(sample_user, db_session)
    payload = {
        "memory_type": "EPISODIC",
        "summary": "Candidate exhibited clear understanding of REST architectural principles.",
        "key_topics": ["REST", "API Design", "HTTP"],
    }
    res = client.post(f"/api/v1/memory/{sample_user.id}", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == sample_user.id
    assert "REST" in data["key_topics"]


def test_get_timeline_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify GET /api/v1/memory/{candidate_id}/timeline."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/memory/{sample_user.id}/timeline", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_get_skills_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify GET /api/v1/memory/{candidate_id}/skills."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/memory/{sample_user.id}/skills", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_get_recommendations_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify GET /api/v1/memory/{candidate_id}/recommendations."""
    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/memory/{sample_user.id}/recommendations", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 4
    assert data[0]["week_number"] == 1


def test_compress_memories_route(client: TestClient, db_session: Session, sample_user: User):
    """Verify POST /api/v1/memory/{candidate_id}/summarize."""
    headers = _auth_headers(sample_user, db_session)
    res = client.post(f"/api/v1/memory/{sample_user.id}/summarize", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == sample_user.id
    assert "compressed_summary" in data


def test_memory_route_ownership_authorization(client: TestClient, db_session: Session, sample_user: User):
    """Verify user A cannot access candidate memory of user B."""
    other_user = User(
        email="other@example.com",
        password_hash="hashed_pass_other",
        full_name="Other User",
    )
    db_session.add(other_user)
    db_session.commit()

    headers = _auth_headers(sample_user, db_session)
    res = client.get(f"/api/v1/memory/{other_user.id}", headers=headers)
    assert res.status_code == 403
