"""
Unit tests for Dynamic Role Resolution (Section 10.9).
Verifies that the interview page and backend endpoints dynamically output the target role from the JD
and never hardcode 'Senior Software Engineer Interview'.
"""

from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.services.interview_service import InterviewService
from app.services.report_service import ReportService


def test_1_jd_role_senior_python_developer(db_session):
    resume = Resume(user_id="user-1", raw_text="Senior Python developer resume", file_path="resume.pdf")
    db_session.add(resume)
    jd = JobDescription(
        user_id="user-1",
        target_role="Senior Python Developer",
        company_name="Tech Corp",
        raw_text="Looking for Senior Python Developer with FastAPI expertise.",
    )
    db_session.add(jd)
    db_session.commit()

    service = InterviewService(db_session)
    interview = service.create_interview("user-1", resume_id=resume.id, jd_id=jd.id)
    assert interview.target_role == "Senior Python Developer"


def test_2_jd_role_backend_engineer(db_session):
    resume = Resume(user_id="user-1", raw_text="Backend developer resume", file_path="resume.pdf")
    db_session.add(resume)
    jd = JobDescription(
        user_id="user-1",
        target_role="Backend Engineer",
        company_name="Acme",
        raw_text="Looking for Backend Engineer.",
    )
    db_session.add(jd)
    db_session.commit()

    service = InterviewService(db_session)
    interview = service.create_interview("user-1", resume_id=resume.id, jd_id=jd.id)
    assert interview.target_role == "Backend Engineer"


def test_3_jd_role_machine_learning_engineer(db_session):
    resume = Resume(user_id="user-1", raw_text="ML developer resume", file_path="resume.pdf")
    db_session.add(resume)
    jd = JobDescription(
        user_id="user-1",
        target_role="Machine Learning Engineer",
        company_name="AI Labs",
        raw_text="Looking for ML Engineer.",
    )
    db_session.add(jd)
    db_session.commit()

    service = InterviewService(db_session)
    interview = service.create_interview("user-1", resume_id=resume.id, jd_id=jd.id)
    assert interview.target_role == "Machine Learning Engineer"


def test_4_no_jd_role_fallback_to_interview(db_session):
    resume = Resume(user_id="user-1", raw_text="Developer resume", file_path="resume.pdf")
    db_session.add(resume)
    jd = JobDescription(
        user_id="user-1",
        target_role="",
        company_name="General",
        raw_text="General job description.",
    )
    db_session.add(jd)
    db_session.commit()

    service = InterviewService(db_session)
    interview = service.create_interview("user-1", resume_id=resume.id, jd_id=jd.id)
    
    report_service = ReportService(db_session)
    resolved_role = report_service._resolve_role(interview.id)
    
    assert resolved_role == "Interview"
    assert resolved_role != "Senior Software Engineer"
    assert resolved_role != "Software Engineer"
