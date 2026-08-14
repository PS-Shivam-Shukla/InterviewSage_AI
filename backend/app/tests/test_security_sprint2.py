"""
Phase 1 - Sprint 2 Security Audit Tests:
1. Resource Ownership Authorization (C-6)
2. Authenticated WebSockets (H-3)
3. File Upload Hardening (H-4)
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Interview, JobDescription, Resume, User
from app.services import AuthService

# ── Helpers ───────────────────────────────────────────────────────────────────

def _create_test_user(db: Session, email: str, name: str) -> tuple[User, str]:
    """Create a user record with explicit UUID and return (user_obj, jwt_token)."""
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=email,
        password_hash="pbkdf2_sha256$test_hash",
        full_name=name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    auth_service = AuthService(db)
    token = auth_service.create_user_token(user)
    return user, token


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── 1. Resource Ownership Authorization Tests (C-6) ───────────────────────────

def test_user_a_cannot_access_user_b_interview(client: TestClient, db_session: Session):
    """Verify HTTP 403 Forbidden when User A attempts to access User B's interview."""
    user_a, token_a = _create_test_user(db_session, "user_a@test.com", "User A")
    user_b, token_b = _create_test_user(db_session, "user_b@test.com", "User B")

    resume_b = Resume(id=str(uuid.uuid4()), user_id=user_b.id, file_path="resume.pdf", raw_text="Resume Text")
    jd_b = JobDescription(id=str(uuid.uuid4()), user_id=user_b.id, raw_text="JD Text", target_role="Engineer")
    db_session.add_all([resume_b, jd_b])
    db_session.commit()

    interview_b = Interview(
        id=str(uuid.uuid4()),
        user_id=user_b.id,
        resume_id=resume_b.id,
        jd_id=jd_b.id,
        status="PLANNING",
    )
    db_session.add(interview_b)
    db_session.commit()

    # User B can access own interview
    res_b = client.get(f"/api/v1/interviews/{interview_b.id}", headers=_auth_header(token_b))
    assert res_b.status_code == 200

    # User A attempting to access User B's interview -> 403 Forbidden
    res_a = client.get(f"/api/v1/interviews/{interview_b.id}", headers=_auth_header(token_a))
    assert res_a.status_code == 403
    assert "Forbidden" in res_a.json()["detail"]


def test_user_a_cannot_access_user_b_report(client: TestClient, db_session: Session):
    """Verify HTTP 403 Forbidden when User A attempts to access User B's report."""
    user_a, token_a = _create_test_user(db_session, "user_a_rpt@test.com", "User A")
    user_b, token_b = _create_test_user(db_session, "user_b_rpt@test.com", "User B")

    resume_b = Resume(id=str(uuid.uuid4()), user_id=user_b.id, file_path="resume.pdf", raw_text="Resume")
    jd_b = JobDescription(id=str(uuid.uuid4()), user_id=user_b.id, raw_text="JD", target_role="Dev")
    db_session.add_all([resume_b, jd_b])
    db_session.commit()

    interview_b = Interview(id=str(uuid.uuid4()), user_id=user_b.id, resume_id=resume_b.id, jd_id=jd_b.id)
    db_session.add(interview_b)
    db_session.commit()

    # User A requesting User B's report -> 403 Forbidden
    res_a = client.get(f"/api/v1/reports/{interview_b.id}", headers=_auth_header(token_a))
    assert res_a.status_code == 403


def test_user_a_cannot_access_user_b_resume(client: TestClient, db_session: Session):
    """Verify HTTP 403 Forbidden when User A attempts to access User B's resume."""
    user_a, token_a = _create_test_user(db_session, "user_a_res@test.com", "User A")
    user_b, token_b = _create_test_user(db_session, "user_b_res@test.com", "User B")

    resume_b = Resume(id=str(uuid.uuid4()), user_id=user_b.id, file_path="resume_b.pdf", raw_text="Resume B")
    db_session.add(resume_b)
    db_session.commit()

    res_a = client.get(f"/api/v1/resumes/{resume_b.id}", headers=_auth_header(token_a))
    assert res_a.status_code == 403


def test_user_a_cannot_access_user_b_job_description(client: TestClient, db_session: Session):
    """Verify HTTP 403 Forbidden when User A attempts to access User B's job description."""
    user_a, token_a = _create_test_user(db_session, "user_a_jd@test.com", "User A")
    user_b, token_b = _create_test_user(db_session, "user_b_jd@test.com", "User B")

    jd_b = JobDescription(id=str(uuid.uuid4()), user_id=user_b.id, raw_text="JD B", target_role="Backend")
    db_session.add(jd_b)
    db_session.commit()

    res_a = client.get(f"/api/v1/job-descriptions/{jd_b.id}", headers=_auth_header(token_a))
    assert res_a.status_code == 403


# ── 2. WebSocket Authentication & Authorization Tests (H-3) ───────────────────

def test_websocket_missing_token(client: TestClient, db_session: Session):
    """Verify WebSocket connection rejected when token is missing."""
    with pytest.raises(Exception), client.websocket_connect("/api/v1/ws/interviews/some-id"):
        pass


def test_websocket_invalid_token(client: TestClient, db_session: Session):
    """Verify WebSocket connection rejected with invalid token."""
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/interviews/some-id?token=invalid.jwt.token"):
            pass


def test_websocket_wrong_ownership_rejected(client: TestClient, db_session: Session):
    """Verify WebSocket connection rejected when user does not own the interview."""
    user_a, token_a = _create_test_user(db_session, "ws_a@test.com", "WS A")
    user_b, token_b = _create_test_user(db_session, "ws_b@test.com", "WS B")

    resume_b = Resume(id=str(uuid.uuid4()), user_id=user_b.id, file_path="r.pdf", raw_text="Text")
    jd_b = JobDescription(id=str(uuid.uuid4()), user_id=user_b.id, raw_text="JD", target_role="Role")
    db_session.add_all([resume_b, jd_b])
    db_session.commit()

    interview_b = Interview(id=str(uuid.uuid4()), user_id=user_b.id, resume_id=resume_b.id, jd_id=jd_b.id)
    db_session.add(interview_b)
    db_session.commit()

    # User A attempting to connect to User B's interview WS -> Rejected
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/interviews/{interview_b.id}?token={token_a}"):
            pass


def test_websocket_valid_connection(client: TestClient, db_session: Session):
    """Verify WebSocket connects cleanly when user owns the interview."""
    user, token = _create_test_user(db_session, "ws_valid@test.com", "WS Valid")
    resume = Resume(id=str(uuid.uuid4()), user_id=user.id, file_path="r.pdf", raw_text="Text")
    jd = JobDescription(id=str(uuid.uuid4()), user_id=user.id, raw_text="JD", target_role="Role")
    db_session.add_all([resume, jd])
    db_session.commit()

    interview = Interview(id=str(uuid.uuid4()), user_id=user.id, resume_id=resume.id, jd_id=jd.id)
    db_session.add(interview)
    db_session.commit()

    with client.websocket_connect(f"/api/v1/ws/interviews/{interview.id}?token={token}") as websocket:
        websocket.send_json({"type": "PING"})
        data = websocket.receive_json()
        assert data["type"] == "PONG"


# ── 3. File Upload Hardening Tests (H-4) ──────────────────────────────────────

def test_upload_empty_file_rejected(client: TestClient, db_session: Session):
    """Verify HTTP 400 Bad Request on empty file upload (0 bytes)."""
    user, token = _create_test_user(db_session, "up_empty@test.com", "User")
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    res = client.post("/api/v1/resumes/", files=files, headers=_auth_header(token))
    assert res.status_code == 400
    assert "File is empty" in res.json()["detail"]


def test_upload_oversized_file_rejected(client: TestClient, db_session: Session, monkeypatch):
    """Verify HTTP 400 Bad Request when file exceeds maximum allowed size."""
    user, token = _create_test_user(db_session, "up_size@test.com", "User")
    monkeypatch.setattr(settings, "max_upload_size", 100)
    big_content = b"A" * 200
    files = {"file": ("large_resume.pdf", big_content, "application/pdf")}
    res = client.post("/api/v1/resumes/", files=files, headers=_auth_header(token))
    assert res.status_code == 400
    assert "File size exceeds maximum allowed limit" in res.json()["detail"]


def test_upload_invalid_mime_rejected(client: TestClient, db_session: Session):
    """Verify HTTP 400 Bad Request for unsupported MIME type."""
    user, token = _create_test_user(db_session, "up_mime@test.com", "User")
    files = {"file": ("resume.pdf", b"fake content", "image/png")}
    res = client.post("/api/v1/resumes/", files=files, headers=_auth_header(token))
    assert res.status_code == 400
    assert "Unsupported MIME type" in res.json()["detail"]


def test_upload_invalid_extension_rejected(client: TestClient, db_session: Session):
    """Verify HTTP 400 Bad Request for unsupported file extension."""
    user, token = _create_test_user(db_session, "up_ext@test.com", "User")
    files = {"file": ("malicious.exe", b"binary content", "application/pdf")}
    res = client.post("/api/v1/resumes/", files=files, headers=_auth_header(token))
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["detail"]


def test_upload_dangerous_filename_rejected(client: TestClient, db_session: Session):
    """Verify HTTP 400 Bad Request for path traversal and double extensions."""
    user, token = _create_test_user(db_session, "up_danger@test.com", "User")
    dangerous_names = [
        "../../../etc/passwd",
        ".bashrc",
        "resume.pdf.exe",
    ]
    for filename in dangerous_names:
        files = {"file": (filename, b"content", "application/pdf")}
        res = client.post("/api/v1/resumes/", files=files, headers=_auth_header(token))
        assert res.status_code == 400
        assert "Dangerous filename detected" in res.json()["detail"] or "Unsupported file extension" in res.json()["detail"]


def test_upload_valid_pdf_accepted(client: TestClient, db_session: Session):
    """Verify successful 201 Created for a valid PDF file upload."""
    user, token = _create_test_user(db_session, "up_valid@test.com", "User")
    files = {"file": ("valid_resume.pdf", b"%PDF-1.4 sample content Python FastAPI", "application/pdf")}
    res = client.post("/api/v1/resumes/", files=files, headers=_auth_header(token))
    assert res.status_code == 201
    assert res.json()["file_path"] == "valid_resume.pdf"
