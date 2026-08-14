"""
Unit and Integration Tests for Admin Dashboard Operations (OP-1 through OP-6, OP-10).
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.admin.dashboard import AdminDashboardManager
from app.models import Interview, JobDescription, Resume, User


def test_admin_dashboard_manager_overview(db_session: Session):
    """Verify AdminDashboardManager overview aggregations."""
    mgr = AdminDashboardManager(db_session)
    overview = mgr.get_dashboard_overview()

    assert "total_interviews" in overview
    assert "active_interviews" in overview
    assert "success_rate" in overview
    assert "avg_latency_ms" in overview
    assert "hallucination_rate" in overview


def test_admin_dashboard_manager_live_interviews(db_session: Session):
    """Verify AdminDashboardManager live interview monitoring list."""
    mgr = AdminDashboardManager(db_session)
    live_items = mgr.get_live_interviews()

    assert len(live_items) > 0
    assert "interview_id" in live_items[0]
    assert "worker_id" in live_items[0]
    assert "thread_id" in live_items[0]


def test_admin_dashboard_manager_timeline_reconstruction(
    db_session: Session, sample_user: User, sample_resume: Resume, sample_jd: JobDescription
):
    """Verify AdminDashboardManager conversation replay timeline reconstruction."""
    iv = Interview(
        user_id=sample_user.id,
        resume_id=sample_resume.id,
        jd_id=sample_jd.id,
        status="COMPLETED",
        overall_score=85,
    )
    db_session.add(iv)
    db_session.commit()

    mgr = AdminDashboardManager(db_session)
    timeline_res = mgr.reconstruct_timeline(iv.id)

    assert timeline_res["interview_id"] == iv.id
    assert "timeline" in timeline_res
    assert isinstance(timeline_res["timeline"], list)


def test_admin_dashboard_prompt_history_explorer(db_session: Session):
    """Verify AdminDashboardManager prompt history explorer."""
    mgr = AdminDashboardManager(db_session)
    history = mgr.get_prompt_history_explorer()

    assert len(history) > 0
    assert "prompt_key" in history[0]
    assert "version" in history[0]


def test_admin_dashboard_route(client: TestClient, admin_token_headers: dict):
    """Verify GET /api/v1/admin/dashboard API endpoint."""
    res = client.get("/api/v1/admin/dashboard", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_interviews" in data
    assert "success_rate" in data


def test_admin_live_interviews_route(client: TestClient, admin_token_headers: dict):
    """Verify GET /api/v1/admin/interviews/live API endpoint."""
    res = client.get("/api/v1/admin/interviews/live", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_admin_timeline_route(
    client: TestClient, admin_token_headers: dict, db_session: Session, sample_user: User, sample_resume: Resume, sample_jd: JobDescription
):
    """Verify GET /api/v1/admin/interview/{id}/timeline API endpoint."""
    iv = Interview(
        user_id=sample_user.id,
        resume_id=sample_resume.id,
        jd_id=sample_jd.id,
        status="COMPLETED",
    )
    db_session.add(iv)
    db_session.commit()

    res = client.get(f"/api/v1/admin/interview/{iv.id}/timeline", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["interview_id"] == iv.id
