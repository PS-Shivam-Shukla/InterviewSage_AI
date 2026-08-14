import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from app.services import AuthService


def auth_headers(user, db_session: Session) -> dict[str, str]:
    token = AuthService(db_session).create_user_token(user)
    return {"Authorization": f"Bearer {token}"}


def test_resume_routes(client: TestClient, db_session: Session, sample_user):
    headers = auth_headers(sample_user, db_session)
    response = client.post(
        "/api/v1/resumes/",
        files={"file": ("resume.txt", b"dummy resume content")},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == sample_user.id
    assert data["parsed_skills"] == []
    assert data["parsed_experience"] == []
    resume_id = data["id"]

    response = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == resume_id


def test_job_description_routes(client: TestClient, db_session: Session, sample_user):
    headers = auth_headers(sample_user, db_session)
    payload = {
        "raw_text": "We need an expert backend engineer.",
        "target_role": "Backend Engineer",
        "company_name": "InterviewSage",
        "industry": "AI",
    }

    response = client.post("/api/v1/job-descriptions/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == sample_user.id
    assert isinstance(data["required_skills"], list)
    assert "seniority_level" in data
    jd_id = data["id"]

    response = client.get(f"/api/v1/job-descriptions/{jd_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == jd_id


def test_interview_routes(
    client: TestClient,
    db_session: Session,
    sample_user,
    sample_resume,
    sample_jd,
):
    headers = auth_headers(sample_user, db_session)
    payload = {"resume_id": sample_resume.id, "jd_id": sample_jd.id}

    response = client.post("/api/v1/interviews/", json=payload, headers=headers)
    assert response.status_code in (200, 201)
    interview = response.json()
    assert interview["status"] == "PLANNING"
    interview_id = interview["id"]

    response = client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == interview_id

    response = client.get(f"/api/v1/interviews/{interview_id}/plan", headers=headers)
    assert response.status_code == 200
    assert response.json()["interview_id"] == interview_id

    response = client.post(
        f"/api/v1/interviews/{interview_id}/answers",
        json={"answer": "I would use dependency injection."},
        headers=headers,
    )
    assert response.status_code == 200
    assert "message" in response.json()

    response = client.post(f"/api/v1/interviews/{interview_id}/pause", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "PAUSED"

    response = client.post(f"/api/v1/interviews/{interview_id}/resume", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


def test_report_routes(client: TestClient, db_session: Session, sample_user, sample_interview):
    headers = auth_headers(sample_user, db_session)

    dummy_uuid = str(uuid.uuid4())
    response = client.get(f"/api/v1/reports/{dummy_uuid}", headers=headers)
    assert response.status_code == 404

    response = client.get(f"/api/v1/reports/{sample_interview.id}/pdf", headers=headers)
    assert response.status_code in (400, 404)

    # Mark interview as COMPLETED for report generation
    sample_interview.status = "COMPLETED"
    db_session.commit()

    # Trigger report generation via the API
    response = client.post(f"/api/v1/reports/{sample_interview.id}/generate", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["interview_id"] == sample_interview.id

    response = client.get(f"/api/v1/reports/{sample_interview.id}/pdf", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == f"attachment; filename=report_{sample_interview.id}.pdf"
    assert response.content.startswith(b"%PDF")
    
    # Verify JSON report endpoint returns the stored report
    response = client.get(f"/api/v1/reports/{sample_interview.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["interview_id"] == sample_interview.id
    assert isinstance(data["competency_scorecard"], list)
    assert data["generated_at"] is not None


def test_user_routes(client: TestClient, db_session: Session, sample_user):
    headers = auth_headers(sample_user, db_session)
    response = client.patch(
        f"/api/v1/users/{sample_user.id}",
        json={"full_name": "Updated Name"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"

    response = client.get(f"/api/v1/users/{sample_user.id}/export", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == sample_user.id
    assert data["email"] == sample_user.email
    assert data["full_name"] == "Updated Name"


def test_analytics_routes(
    client: TestClient,
    db_session: Session,
    sample_user,
    sample_resume,
    sample_jd,
):
    headers = auth_headers(sample_user, db_session)
    response = client.post(
        "/api/v1/interviews/",
        json={"resume_id": sample_resume.id, "jd_id": sample_jd.id},
        headers=headers,
    )
    assert response.status_code in (200, 201)

    response = client.get("/api/v1/analytics/summary", headers=headers)
    assert response.status_code == 200
    assert response.json()["summary"]["total_interviews"] == 1

    response = client.get("/api/v1/analytics/trends", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json()["trends"], list)

    response = client.get("/api/v1/analytics/competencies", headers=headers)
    assert response.status_code == 200
    assert response.json()["competencies"] == []


def test_admin_route_requires_admin(client: TestClient, db_session: Session, sample_user):
    headers = auth_headers(sample_user, db_session)
    response = client.get("/api/v1/admin/agent-metrics", headers=headers)
    assert response.status_code == 403


def test_admin_route_admin_user(client: TestClient, db_session: Session):
    admin_user = User(
        email="admin@example.com",
        password_hash="hashed_admin_password",
        full_name="Admin User",
    )
    db_session.add(admin_user)
    db_session.commit()
    headers = auth_headers(admin_user, db_session)

    response = client.get("/api/v1/admin/agent-metrics", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"metrics": []}
