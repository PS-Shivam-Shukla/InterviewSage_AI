"""
Deterministic Unit Tests for SupervisorAgent (Phase 4C).
Covers all 20 specified state transitions, prerequisite checks, failure retries, and immutable protections.
Uses 100% deterministic test logic with zero external LLM calls.
"""

import pytest

from app.agents.supervisor_agent import SupervisorAgent, WorkflowState
from app.graph.state import InterviewState
from app.schemas.agent_contracts import AgentError, AgentErrorCode, AgentResult


@pytest.fixture
def supervisor():
    return SupervisorAgent(max_retries=2)


# 1. Initial state routing
def test_initial_state_routing(supervisor):
    state: InterviewState = {
        "workflow_stage": "INITIALIZING",
        "resume_raw_text": "Python Developer Resume",
    }
    next_node = supervisor.decide_next_step(state)
    assert next_node == "resume_agent"


# 2. Resume -> JD transition
def test_resume_to_jd_transition(supervisor):
    state: InterviewState = {
        "workflow_stage": "RESUME_ANALYSIS",
        "resume_data": {"skills": ["Python"]},
    }
    next_node = supervisor.decide_next_step(state)
    assert next_node == "jd_agent"


# 3. JD -> planning transition
def test_jd_to_planning_transition(supervisor):
    state: InterviewState = {
        "workflow_stage": "JD_ANALYSIS",
        "jd_data": {"target_role": "Backend Engineer"},
    }
    next_node = supervisor.decide_next_step(state)
    assert next_node == "interview_planner_agent"


# 4. Planning -> question generation
def test_planning_to_question_generation(supervisor):
    state: InterviewState = {
        "workflow_stage": "INTERVIEW_PLANNING",
        "interview_plan": {"total_questions": 3, "technical_question_count": 3},
        "current_round": "TECHNICAL",
    }
    next_node = supervisor.decide_next_step(state)
    assert next_node == "question_generator_tech"


# 5. Question -> waiting for answer
def test_question_to_waiting_for_answer(supervisor):
    state: InterviewState = {
        "workflow_stage": "QUESTION_GENERATION",
        "current_question": {"question_text": "What is IoC?"},
    }
    next_node = supervisor.decide_next_step(state)
    assert next_node == "WAIT"


# 6. Answer -> evaluation
def test_answer_to_evaluation(supervisor):
    state: InterviewState = {
        "workflow_stage": "WAITING_FOR_ANSWER",
        "current_round": "TECHNICAL",
        "answers": [{"answer_text": "Inversion of Control"}],
        "current_question": {"question_text": "What is IoC?"},
    }
    next_node = supervisor.decide_next_step(state)
    assert next_node == "evaluation_agent_tech"


# 7. Evaluation -> next question
def test_evaluation_to_next_question(supervisor):
    state: InterviewState = {
        "workflow_stage": "ANSWER_EVALUATION",
        "interview_plan": {"technical_question_count": 3},
        "current_round": "TECHNICAL",
        "questions_asked": [{"q": 1}],  # 1 asked, target 3
    }
    next_node = supervisor.decide_next_step(state)
    assert next_node == "question_generator_tech"


# 8. Last question -> round complete
def test_last_question_round_complete(supervisor):
    state: InterviewState = {
        "workflow_stage": "ANSWER_EVALUATION",
        "interview_plan": {"technical_question_count": 3},
        "current_round": "TECHNICAL",
        "questions_asked": [{"q": 1}, {"q": 2}, {"q": 3}],  # 3 asked, target 3
    }
    next_node = supervisor.decide_next_step(state)
    assert next_node == "report_generator_agent"


# 9. Round complete -> next round
def test_round_complete_to_next_round(supervisor):
    # Transition validation test
    assert supervisor.validate_transition(WorkflowState.ROUND_COMPLETE.value, WorkflowState.NEXT_ROUND.value) is True


# 10. Final round -> interview complete
def test_final_round_interview_complete(supervisor):
    assert supervisor.validate_transition(WorkflowState.ROUND_COMPLETE.value, WorkflowState.INTERVIEW_COMPLETED.value) is True


# 11. Interview complete -> report generation
def test_interview_complete_report_generation(supervisor):
    assert supervisor.validate_transition(WorkflowState.INTERVIEW_COMPLETED.value, WorkflowState.REPORT_GENERATION.value) is True


# 12. Report -> completed
def test_report_to_completed(supervisor):
    state: InterviewState = {
        "workflow_stage": "REPORT_GENERATION",
        "final_report": {"overall_score": 85},
    }
    next_node = supervisor.decide_next_step(state)
    assert next_node == "COMPLETED"


# 13. Invalid transition rejection
def test_invalid_transition_rejection(supervisor):
    # Cannot jump directly from INITIALIZING to COMPLETED
    assert supervisor.validate_transition("INITIALIZING", "COMPLETED") is False


# 14. Missing context failure
def test_missing_context_failure(supervisor):
    state: InterviewState = {
        "workflow_stage": "INITIALIZING",
        # Missing resume_raw_text
    }
    valid, err = supervisor.validate_prerequisites("RESUME_ANALYSIS", state)
    assert valid is False
    assert "Missing resume_raw_text" in err


# 15. Retry behavior
def test_retry_behavior(supervisor):
    state: InterviewState = {
        "workflow_stage": "RESUME_ANALYSIS",
        "retry_count_this_node": 0,
    }
    err = AgentError(
        code=AgentErrorCode.LLM_TIMEOUT,
        message="Ollama timeout",
        retryable=True,
        agent_name="ResumeAgent",
    )
    result = supervisor.handle_failure(state, err)
    assert result["retry_count_this_node"] == 1
    assert "workflow_stage" not in result  # Not failed yet


# 16. Maximum retry protection
def test_max_retry_protection(supervisor):
    state: InterviewState = {
        "workflow_stage": "RESUME_ANALYSIS",
        "retry_count_this_node": 2,  # Already hit max_retries
    }
    err = AgentError(
        code=AgentErrorCode.LLM_TIMEOUT,
        message="Ollama timeout persistent",
        retryable=True,
        agent_name="ResumeAgent",
    )
    result = supervisor.handle_failure(state, err)
    assert result["workflow_stage"] == WorkflowState.FAILED.value


# 17. AgentResult success handling
def test_agent_result_success_handling(supervisor):
    res = AgentResult[dict](
        success=True,
        agent_name="ResumeAgent",
        data={"summary": "Candidate Summary"},
    )
    assert res.success is True
    assert res.error is None


# 18. AgentResult failure handling
def test_agent_result_failure_handling(supervisor):
    err = AgentError(
        code=AgentErrorCode.VALIDATION_ERROR,
        message="Schema validation error",
        retryable=True,
        agent_name="ResumeAgent",
    )
    res = AgentResult[dict](
        success=False,
        agent_name="ResumeAgent",
        error=err,
    )
    assert res.success is False
    assert res.error.code == AgentErrorCode.VALIDATION_ERROR


# 19. Immutable context protection
def test_immutable_context_protection(supervisor):
    original_state: InterviewState = {
        "interview_id": "int-1001",
        "user_id": "usr-500",
        "raw_resume_file_path": "/uploads/resume.pdf",
    }
    malicious_updates = {
        "interview_id": "HACKED_ID",
        "user_id": "HACKED_USER",
        "workflow_stage": "RESUME_ANALYSIS",
    }
    sanitized = supervisor.protect_immutable_context(original_state, malicious_updates)
    assert "interview_id" not in sanitized
    assert "user_id" not in sanitized
    assert sanitized["workflow_stage"] == "RESUME_ANALYSIS"


# 20. Unknown state handling
def test_unknown_state_handling(supervisor):
    state: InterviewState = {
        "workflow_stage": "CORRUPTED_UNKNOWN_STATE",
    }
    next_node = supervisor.decide_next_step(state)
    assert next_node == "FAILED"
