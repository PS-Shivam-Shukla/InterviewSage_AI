"""
Unit and Integration Tests for Human Review Queue & Recruiter Feedback (OP-7, OP-8).
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.review.service import ReviewService


def test_review_service_flag_and_process(db_session: Session):
    """Verify ReviewService flags items for review and updates status."""
    service = ReviewService(db_session)
    item = service.flag_for_review(
        interview_id="int-review-101",
        confidence=0.42,
        reason="Low technical concept confidence score",
    )

    assert item.id is not None
    assert item.interview_id == "int-review-101"
    assert item.status == "PENDING"

    # Get queue
    queue = service.get_queue(status="PENDING")
    assert len(queue) >= 1

    # Update status
    updated = service.process_review(item.id, status="APPROVED", admin_id="admin-001")
    assert updated is not None
    assert updated.status == "APPROVED"
    assert updated.assigned_admin == "admin-001"


def test_review_service_recruiter_feedback(db_session: Session):
    """Verify ReviewService records recruiter qualitative feedback."""
    service = ReviewService(db_session)
    fb = service.record_feedback(
        interview_id="int-feedback-101",
        recruiter_id="recruiter-99",
        rating_action="APPROVE",
        comment="Strong response on distributed consensus.",
    )

    assert fb.id is not None
    assert fb.rating_action == "APPROVE"


def test_admin_review_queue_route(
    client: TestClient, admin_token_headers: dict, db_session: Session
):
    """Verify GET /api/v1/admin/review/queue API endpoint."""
    service = ReviewService(db_session)
    service.flag_for_review(interview_id="int-api-test", confidence=0.3)

    res = client.get("/api/v1/admin/review/queue", headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_admin_feedback_route(client: TestClient, admin_token_headers: dict):
    """Verify POST /api/v1/admin/feedback API endpoint."""
    payload = {
        "interview_id": "int-fb-route-1",
        "rating_action": "APPROVE",
        "comment": "Accurate agent evaluation.",
    }

    res = client.post("/api/v1/admin/feedback", json=payload, headers=admin_token_headers)
    assert res.status_code == 200
    data = res.json()
    assert "feedback_id" in data
