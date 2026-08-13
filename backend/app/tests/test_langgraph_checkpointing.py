"""
Phase 3 - Sprint 6: LangGraph Durable Checkpointing Tests.
Verifies thread configuration, state resumption across turns, recovery after restart, and failure handling.
"""

import uuid
import pytest
from sqlalchemy.orm import Session
from langgraph.checkpoint.memory import MemorySaver

from app.graph.workflow_master import build_master_workflow, get_checkpointer
from app.models import User, Resume, JobDescription, Interview
from app.services.interview_service import InterviewService


def test_graph_compiled_with_checkpointer():
    """Verify master_workflow is compiled with an active checkpointer."""
    checkpointer = MemorySaver()
    workflow = build_master_workflow(checkpointer=checkpointer)
    assert workflow is not None
    assert hasattr(workflow, "checkpointer")
    assert workflow.checkpointer is checkpointer


def test_get_checkpointer_factory():
    """Verify get_checkpointer factory returns MemorySaver for SQLite/test URLs."""
    cp_sqlite = get_checkpointer("sqlite:///:memory:")
    assert isinstance(cp_sqlite, MemorySaver)

    cp_default = get_checkpointer()
    assert cp_default is not None


def test_thread_config_state_resumption():
    """Verify state is checkpointed and resumed using interview.id as thread_id."""
    checkpointer = MemorySaver()
    workflow = build_master_workflow(checkpointer=checkpointer)

    interview_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": interview_id}}

    initial_state = {
        "interview_id": interview_id,
        "resume_json": {"skills": ["Python", "FastAPI"]},
        "jd_json": {"target_role": "Backend Engineer"},
    }

    # Turn 1: Initial invocation
    out1 = workflow.invoke(initial_state, config=config)
    assert out1.get("workflow_stage") is not None

    # Checkpoint retrieval
    state_snapshot = workflow.get_state(config)
    assert state_snapshot is not None
    assert state_snapshot.values.get("interview_id") == interview_id

    # Turn 2: Subsequent invocation using same thread_id config resumes existing checkpoint
    out2 = workflow.invoke({"pending_answer": "I use connection pooling with pre-ping."}, config=config)
    assert out2.get("workflow_stage") is not None


def test_checkpoint_recovery_after_simulated_restart(db_session: Session):
    """Verify interview state recovers cleanly after a simulated application restart."""
    user = User(id=str(uuid.uuid4()), email="restart_test@test.com", password_hash="hash", full_name="Restart Test")
    resume = Resume(id=str(uuid.uuid4()), user_id=user.id, file_path="r.pdf", raw_text="Resume")
    jd = JobDescription(id=str(uuid.uuid4()), user_id=user.id, raw_text="JD", target_role="Senior Python Dev")
    db_session.add_all([user, resume, jd])
    db_session.commit()

    interview = Interview(id=str(uuid.uuid4()), user_id=user.id, resume_id=resume.id, jd_id=jd.id)
    db_session.add(interview)
    db_session.commit()

    service = InterviewService(db_session)

    # 1. Generate plan & initial state
    plan_resp = service.get_interview_plan(interview.id)
    assert plan_resp["interview_id"] == interview.id

    # 2. Simulate application restart (Re-instantiate service and re-query plan)
    new_service = InterviewService(db_session)
    resumed_plan = new_service.get_interview_plan(interview.id)

    assert resumed_plan is not None
    assert resumed_plan["interview_id"] == interview.id
    assert resumed_plan["plan"]["role"] == plan_resp["plan"]["role"]
    assert len(resumed_plan["plan"]["blueprint_items"]) == len(plan_resp["plan"]["blueprint_items"])


def test_missing_thread_id_checkpoint_handling():
    """Verify behavior when querying state for a non-existent or invalid thread ID."""
    checkpointer = MemorySaver()
    workflow = build_master_workflow(checkpointer=checkpointer)

    invalid_config = {"configurable": {"thread_id": "non-existent-thread-id"}}
    snapshot = workflow.get_state(invalid_config)

    assert snapshot is not None
    assert snapshot.values == {}
