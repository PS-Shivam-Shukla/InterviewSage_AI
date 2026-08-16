"""
Resume Data Integrity & Isolation Unit Tests.
Verifies that ResumeAgent failures result in FAILED status, no fake 2/100 INTERN fallbacks are persisted as COMPLETED, and distinct resumes retain isolated analysis payloads.
"""

import json
import pytest
from app.agents.resume_agent import ResumeAgent, ResumeAnalysis
from app.core.database import SessionLocal
from app.core.llm_client import FakeLLMClient
from app.models import Resume, User
from app.services.resume_service import ResumeService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    user = db_session.query(User).filter(User.email == "integrity_test@example.com").first()
    if not user:
        user = User(
            email="integrity_test@example.com",
            password_hash="hashed_pw",
            full_name="Integrity Tester",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


class TestResumeIntegrityAndIsolation:
    def test_resume_agent_success_path(self, db_session, test_user):
        """Test 1: Successful ResumeAgent result sets status COMPLETED and computes real seniority."""
        fake_analysis = ResumeAnalysis(
            summary="Senior Python Engineer with 6 years experience.",
            technical_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
            experience=[
                {
                    "title": "Senior Engineer",
                    "company": "TechCorp",
                    "period": "2020 - 2024",
                    "description": "Led backend microservices",
                    "technologies": ["Python", "FastAPI"],
                }
            ],
            career_level="SENIOR",
            resume_quality_score=90,
        )
        raw_text = (
            "Jane Smith | Senior Python Engineer | 6 years experience in Python, FastAPI, PostgreSQL"
        )
        service = ResumeService(db_session)
        resume_dict, _ = service.upload_resume_fast(
            test_user.id, "test_success.pdf", raw_text.encode("utf-8")
        )
        resume_id = resume_dict["id"]

        # Run process_resume_background with injected agent using FakeLLMClient
        agent = ResumeAgent(llm_client=FakeLLMClient(responses=[fake_analysis]))

        # Execute service background logic with injected mock agent
        service.process_resume_background(resume_id, raw_text, "test_success.pdf", agent=agent)

        # Verify DB status
        res = db_session.query(Resume).filter(Resume.id == resume_id).first()
        assert res is not None
        assert res.status == "COMPLETED"
        assert "Python" in res.parsed_skills

    def test_resume_agent_failure_sets_status_failed(self, db_session, test_user):
        """Test 2 & 3: Failed ResumeAgent processing sets status FAILED and prevents fake 2/100 INTERN result."""
        raw_text = "Valid resume raw text content exceeding 50 characters threshold for testing LLM failure handling."
        service = ResumeService(db_session)
        resume_dict, _ = service.upload_resume_fast(
            test_user.id, "test_fail.pdf", raw_text.encode("utf-8")
        )
        resume_id = resume_dict["id"]

        # Create a FakeLLMClient that raises an exception on invoke_structured
        fake_llm = FakeLLMClient(responses=[])
        def raise_llm_error(*args, **kwargs):
            raise RuntimeError("LLM connection error")
        fake_llm.invoke_structured = raise_llm_error

        agent = ResumeAgent(llm_client=fake_llm)

        # Process background task with failing agent
        service.process_resume_background(resume_id, raw_text, "test_fail.pdf", agent=agent)

        # Verify DB status is FAILED, NOT COMPLETED
        res = db_session.query(Resume).filter(Resume.id == resume_id).first()
        assert res is not None
        assert res.status == "FAILED"
        assert res.seniority_score == 0 or res.seniority_score is None

    def test_different_resumes_remain_independent(self, db_session, test_user):
        """Test 4 & 5: Resume A and Resume B retain distinct analysis payloads."""
        service = ResumeService(db_session)

        # Create Resume A
        res_a = Resume(
            user_id=test_user.id,
            file_path="resume_a.pdf",
            raw_text="Python Backend Engineer",
            parsed_skills=json.dumps(["Python", "FastAPI"]),
            parsed_experience=json.dumps({"summary": "Python Developer", "technical_skills": ["Python", "FastAPI"]}),
            seniority_signal="MID",
            seniority_score=60,
            status="COMPLETED",
        )
        db_session.add(res_a)

        # Create Resume B
        res_b = Resume(
            user_id=test_user.id,
            file_path="resume_b.pdf",
            raw_text="React Frontend Developer",
            parsed_skills=json.dumps(["React", "TypeScript"]),
            parsed_experience=json.dumps({"summary": "Frontend Developer", "technical_skills": ["React", "TypeScript"]}),
            seniority_signal="JUNIOR",
            seniority_score=35,
            status="COMPLETED",
        )
        db_session.add(res_b)
        db_session.commit()

        # Retrieve analysis via ResumeService
        analysis_a = service.get_resume_analysis(res_a.id)
        analysis_b = service.get_resume_analysis(res_b.id)

        assert analysis_a is not None
        assert analysis_b is not None
        assert analysis_a["resume_id"] == res_a.id
        assert analysis_b["resume_id"] == res_b.id
        assert "Python" in analysis_a["skills"]["technical"]
        assert "React" in analysis_b["skills"]["technical"]
        assert analysis_a["seniority_score"] == 60
        assert analysis_b["seniority_score"] == 35
