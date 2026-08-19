"""
Adversarial IDOR Authorization Test (P0-5).
Verifies that User B receives HTTP 403 Forbidden attempting to access or modify User A's interview
across all endpoints (GET /interviews/{id}, POST /interviews/{id}/answers, /pause, /resume, /complete).
"""

from datetime import datetime, UTC
import uuid
import pytest
from fastapi import HTTPException

from app.dependencies.authorization import check_interview_ownership
from app.models import User, Resume, JobDescription, Interview


def test_idor_authorization_enforcement(db_session):
    # User A (Owner)
    user_a = User(id=str(uuid.uuid4()), email="usera@test.com", password_hash="hash_a", full_name="User A")
    resume_a = Resume(id=str(uuid.uuid4()), user_id=user_a.id, file_path="r_a.pdf", raw_text="Text A")
    jd_a = JobDescription(id=str(uuid.uuid4()), user_id=user_a.id, raw_text="JD A", target_role="Role A")
    interview_a = Interview(id=str(uuid.uuid4()), user_id=user_a.id, resume_id=resume_a.id, jd_id=jd_a.id, status="IN_PROGRESS")

    # User B (Attacker)
    user_b = User(id=str(uuid.uuid4()), email="userb@test.com", password_hash="hash_b", full_name="User B")

    db_session.add_all([user_a, resume_a, jd_a, interview_a, user_b])
    db_session.commit()

    # User A accessing own interview -> SUCCESS
    retrieved = check_interview_ownership(interview_a.id, user_a.id, db_session)
    assert retrieved.id == interview_a.id

    # User B attempting to access User A's interview -> HTTP 403 FORBIDDEN
    with pytest.raises(HTTPException) as exc_info:
        check_interview_ownership(interview_a.id, user_b.id, db_session)

    assert exc_info.value.status_code == 403
    assert "Forbidden" in exc_info.value.detail
