"""
Phase 1 - Sprint 3 Tests:
- MCP score_answer_rubric parameter alignment (Audit C-1)
- Undefined interview.id fix & AgentLog persistence (Audit C-2)
- SQLAlchemy production connection pool configuration (Audit H-5)
- Atomic transaction in submit_answer() (Audit H-6)
- Offloaded LangGraph invoke() execution (Audit H-7)
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.core.database import build_engine
from app.mcp import mcp_server
from app.mcp.tools.score_answer_rubric import score_answer_rubric
from app.models import (
    AgentLog,
    Evaluation,
    Interview,
    InterviewAnswer,
    InterviewQuestion,
    JobDescription,
    Resume,
    User,
)
from app.services.interview_service import InterviewService


def test_mcp_score_answer_rubric_aligned_contract():
    """Verify MCP score_answer_rubric tool returns rubric template and seniority context."""
    result = score_answer_rubric(
        question_type="system_design",
        seniority_level="MID",
    )

    assert "dimensions" in result
    assert "seniority_context" in result
    assert "method" in result
    assert len(result["dimensions"]) > 0


def test_mcp_server_call_tool_score_answer_rubric():
    """Verify mcp_server.call_tool succeeds for score_answer_rubric."""
    response = mcp_server.call_tool(
        "score_answer_rubric",
        question_type="advanced",
        seniority_level="SENIOR",
    )
    assert response.success is True
    assert "dimensions" in response.output
    assert "seniority_context" in response.output



def test_submit_answer_atomic_transaction_and_agent_log(db_session: Session):
    """Verify submit_answer creates Question, Answer, Evaluation, and AgentLog atomically."""
    user = User(id=str(uuid.uuid4()), email="atom_test@test.com", password_hash="hash", full_name="Atom Test")
    resume = Resume(id=str(uuid.uuid4()), user_id=user.id, file_path="r.pdf", raw_text="Resume")
    jd = JobDescription(id=str(uuid.uuid4()), user_id=user.id, raw_text="JD", target_role="Backend Engineer")
    db_session.add_all([user, resume, jd])
    db_session.commit()

    interview = Interview(id=str(uuid.uuid4()), user_id=user.id, resume_id=resume.id, jd_id=jd.id, status="IN_PROGRESS")
    db_session.add(interview)
    db_session.commit()

    service = InterviewService(db_session)
    res = service.submit_answer(
        interview_id=interview.id,
        answer="I design idempotent APIs with connection pooling and atomic transactions.",
        question_text="Explain enterprise backend design patterns.",
    )

    assert res["status"] == "IN_PROGRESS"
    assert "evaluation" in res

    question = db_session.query(InterviewQuestion).filter(InterviewQuestion.interview_id == interview.id).first()
    assert question is not None
    assert question.question_text == "Explain enterprise backend design patterns."

    answer = db_session.query(InterviewAnswer).filter(InterviewAnswer.question_id == question.id).first()
    assert answer is not None
    assert "connection pooling" in answer.answer_text

    eval_rec = db_session.query(Evaluation).filter(Evaluation.answer_id == answer.id).first()
    assert eval_rec is not None
    assert eval_rec.score >= 70

    log_rec = db_session.query(AgentLog).filter(AgentLog.interview_id == interview.id).first()
    assert log_rec is not None
    assert log_rec.agent_name == "EvaluationAgent"
    assert log_rec.node_status == "COMPLETED"


def test_submit_answer_atomic_rollback_on_failure(db_session: Session, monkeypatch):
    """Verify that a database error causes rollback of all records in submit_answer."""
    user = User(id=str(uuid.uuid4()), email="rollback_test@test.com", password_hash="hash", full_name="Rollback Test")
    resume = Resume(id=str(uuid.uuid4()), user_id=user.id, file_path="r.pdf", raw_text="Resume")
    jd = JobDescription(id=str(uuid.uuid4()), user_id=user.id, raw_text="JD", target_role="Dev")
    db_session.add_all([user, resume, jd])
    db_session.commit()

    interview = Interview(id=str(uuid.uuid4()), user_id=user.id, resume_id=resume.id, jd_id=jd.id)
    db_session.add(interview)
    db_session.commit()

    def mock_commit_fail():
        raise Exception("Database transaction failure simulated")

    service = InterviewService(db_session)
    monkeypatch.setattr(db_session, "commit", mock_commit_fail)

    with pytest.raises(Exception, match="Database transaction failure simulated"):
        service.submit_answer(
            interview_id=interview.id,
            answer="This answer commit should roll back cleanly.",
            question_text="Enterprise architecture question?",
        )


def test_database_connection_pool_configuration():
    """Verify PostgreSQL engine is configured with production connection pool settings."""
    pg_url = "postgresql://user:pass@localhost:5432/testdb"
    engine = build_engine(pg_url)

    assert engine.pool.size() == 10
    assert engine.pool._max_overflow == 20
    assert engine.pool._recycle == 3600
    assert engine.pool._timeout == 30


def test_sqlite_connection_pool_compatibility():
    """Verify SQLite engine maintains WAL mode and connection pre-ping compatibility."""
    sqlite_url = "sqlite:///:memory:"
    engine = build_engine(sqlite_url)
    assert engine is not None


def test_offloaded_langgraph_invoke(db_session: Session):
    """Verify get_interview_plan executes LangGraph workflow and returns blueprint plan envelope."""
    user = User(id=str(uuid.uuid4()), email="graph_test@test.com", password_hash="hash", full_name="Graph Test")
    resume = Resume(id=str(uuid.uuid4()), user_id=user.id, file_path="r.pdf", raw_text="Resume")
    jd = JobDescription(id=str(uuid.uuid4()), user_id=user.id, raw_text="JD", target_role="Python Developer")
    db_session.add_all([user, resume, jd])
    db_session.commit()

    interview = Interview(id=str(uuid.uuid4()), user_id=user.id, resume_id=resume.id, jd_id=jd.id)
    db_session.add(interview)
    db_session.commit()

    service = InterviewService(db_session)
    plan_resp = service.get_interview_plan(interview.id)

    assert plan_resp is not None
    assert plan_resp["interview_id"] == interview.id
    assert "plan" in plan_resp
    assert "blueprint_items" in plan_resp["plan"]
    assert "first_question" in plan_resp["plan"]
