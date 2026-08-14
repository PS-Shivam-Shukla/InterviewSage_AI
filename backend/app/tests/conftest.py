"""
Pytest configuration and shared fixtures.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.repositories import (
    UserRepository,
    ResumeRepository,
    JobDescriptionRepository,
    InterviewRepository,
    CompetencyMatrixRepository,
    InterviewPlanRepository,
    InterviewQuestionRepository,
    InterviewAnswerRepository,
    EvaluationRepository,
    InterviewReportRepository,
    AgentLogRepository,
)
from fastapi.testclient import TestClient
from app.core.database import get_db
from app.main import app


@pytest.fixture(autouse=True)
def mock_llm_agents(monkeypatch):
    """Mock LLM agents in pytest environment so tests run offline deterministically."""
    try:
        from app.agents.question_generator_agent import QuestionGeneratorAgent
        from app.agents.evaluation_agent import EvaluationAgent

        orig_eval_call = EvaluationAgent.__call__
        orig_gen_call = QuestionGeneratorAgent.__call__

        def mock_eval_call(self, state):
            answers = state.get("answers") or []
            if not answers:
                return {}
            if getattr(self, "llm", None) is not None:
                return orig_eval_call(self, state)
            current_q = state.get("current_question") or {}
            round_type = (current_q.get("round_type") or (answers[-1].get("round_type") if answers else "") or "").upper()
            if round_type == "APTITUDE":
                return orig_eval_call(self, state)
            return {
                "evaluations": [{
                    "score": 90,
                    "rubric_breakdown": {"Technical Depth": 5, "Problem Solving": 4},
                    "feedback": "Evaluated via EvaluationAgent test double.",
                    "reasoning": "Evaluated via EvaluationAgent test double.",
                    "ideal_answer_summary": "Comprehensive architectural solution.",
                    "answer_quality": "VALID_ANSWER",
                }]
            }

        def mock_gen_call(self, state):
            if getattr(self, "llm", None) is not None:
                return orig_gen_call(self, state)
            r_type = getattr(self, "round_type", "TECHNICAL")
            return {
                "current_question": {
                    "question_text": f"Mock {r_type} Question Text?",
                    "competency_targeted": "System Architecture" if r_type == "TECHNICAL" else "Leadership & Culture",
                    "difficulty": "MEDIUM",
                    "question_type": r_type.lower(),
                }
            }

        monkeypatch.setattr(EvaluationAgent, "__call__", mock_eval_call)
        monkeypatch.setattr(QuestionGeneratorAgent, "__call__", mock_gen_call)
    except Exception:
        pass


@pytest.fixture(scope="function")
def db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def user_repo(db_session):
    """User repository fixture."""
    return UserRepository(db_session)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with database dependency override."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def resume_repo(db_session):
    """Resume repository fixture."""
    return ResumeRepository(db_session)


@pytest.fixture(scope="function")
def jd_repo(db_session):
    """JobDescription repository fixture."""
    return JobDescriptionRepository(db_session)


@pytest.fixture(scope="function")
def interview_repo(db_session):
    """Interview repository fixture."""
    return InterviewRepository(db_session)


@pytest.fixture(scope="function")
def competency_matrix_repo(db_session):
    """CompetencyMatrix repository fixture."""
    return CompetencyMatrixRepository(db_session)


@pytest.fixture(scope="function")
def interview_plan_repo(db_session):
    """InterviewPlan repository fixture."""
    return InterviewPlanRepository(db_session)


@pytest.fixture(scope="function")
def question_repo(db_session):
    """InterviewQuestion repository fixture."""
    return InterviewQuestionRepository(db_session)


@pytest.fixture(scope="function")
def answer_repo(db_session):
    """InterviewAnswer repository fixture."""
    return InterviewAnswerRepository(db_session)


@pytest.fixture(scope="function")
def evaluation_repo(db_session):
    """Evaluation repository fixture."""
    return EvaluationRepository(db_session)


@pytest.fixture(scope="function")
def report_repo(db_session):
    """InterviewReport repository fixture."""
    return InterviewReportRepository(db_session)


@pytest.fixture(scope="function")
def agent_log_repo(db_session):
    """AgentLog repository fixture."""
    return AgentLogRepository(db_session)


# Sample data fixtures
@pytest.fixture(scope="function")
def sample_user(db_session):
    """Create a sample user."""
    from app.models import User
    user = User(
        email="test@example.com",
        password_hash="hashed_password_123",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def admin_user(db_session):
    """Create an admin user."""
    from app.models import User
    user = User(
        email="admin@example.com",
        password_hash="hashed_password_admin_123",
        full_name="Admin User",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def admin_token_headers(db_session, admin_user):
    """Auth token headers for admin user."""
    from app.services import AuthService
    token = AuthService(db_session).create_user_token(admin_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_resume(db_session, sample_user):
    """Create a sample resume."""
    from app.models import Resume
    resume = Resume(
        user_id=sample_user.id,
        file_path="/uploads/test_resume.pdf",
        raw_text="Backend engineer with 5 years experience",
        parsed_skills="[\"Python\", \"FastAPI\", \"PostgreSQL\"]",
        parsed_experience="[{\"company\": \"TechCorp\", \"role\": \"Senior Backend Engineer\"}]",
        seniority_signal="SENIOR",
    )
    db_session.add(resume)
    db_session.commit()
    return resume


@pytest.fixture(scope="function")
def sample_jd(db_session, sample_user):
    """Create a sample job description."""
    from app.models import JobDescription
    jd = JobDescription(
        user_id=sample_user.id,
        raw_text="We are looking for a Python backend engineer",
        target_role="Senior Backend Engineer",
        company_name="StartupXYZ",
        industry="FinTech",
        required_skills="[\"Python\", \"FastAPI\", \"PostgreSQL\", \"Redis\"]",
        seniority_level="SENIOR",
    )
    db_session.add(jd)
    db_session.commit()
    return jd


@pytest.fixture(scope="function")
def sample_interview(db_session, sample_user, sample_resume, sample_jd):
    """Create a sample interview."""
    from datetime import datetime, timezone
    from app.models import Interview
    interview = Interview(
        user_id=sample_user.id,
        resume_id=sample_resume.id,
        jd_id=sample_jd.id,
        status="PLANNING",
        current_round=None,
        overall_score=None,
        started_at=datetime.now(timezone.utc),
        completed_at=None,
    )
    db_session.add(interview)
    db_session.commit()
    return interview
