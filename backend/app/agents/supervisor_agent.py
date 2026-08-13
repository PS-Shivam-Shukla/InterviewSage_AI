"""
Supervisor Agent (Phase 4C) — Deterministic Orchestrator & State Machine.
Manages workflow transitions, prerequisite validations, state routing, retry limits, and error handling.
Does NOT execute LLM calls directly; delegates all domain reasoning to specialist sub-agents.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.logging import get_logger
from app.graph.state import InterviewState
from app.schemas.agent_contracts import AgentError, AgentErrorCode, AgentResult

logger = get_logger(__name__)

MAX_RETRIES = 2


class WorkflowState(str, Enum):
    INITIALIZING = "INITIALIZING"
    RESUME_ANALYSIS = "RESUME_ANALYSIS"
    JD_ANALYSIS = "JD_ANALYSIS"
    INTERVIEW_PLANNING = "INTERVIEW_PLANNING"
    READY = "READY"
    QUESTION_GENERATION = "QUESTION_GENERATION"
    WAITING_FOR_ANSWER = "WAITING_FOR_ANSWER"
    ANSWER_EVALUATION = "ANSWER_EVALUATION"
    NEXT_QUESTION = "NEXT_QUESTION"
    ROUND_COMPLETE = "ROUND_COMPLETE"
    NEXT_ROUND = "NEXT_ROUND"
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED"
    REPORT_GENERATION = "REPORT_GENERATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Deterministic state transition table
ALLOWED_TRANSITIONS: Dict[WorkflowState, Set[WorkflowState]] = {
    WorkflowState.INITIALIZING: {WorkflowState.RESUME_ANALYSIS, WorkflowState.FAILED},
    WorkflowState.RESUME_ANALYSIS: {WorkflowState.JD_ANALYSIS, WorkflowState.FAILED},
    WorkflowState.JD_ANALYSIS: {WorkflowState.INTERVIEW_PLANNING, WorkflowState.FAILED},
    WorkflowState.INTERVIEW_PLANNING: {WorkflowState.READY, WorkflowState.FAILED},
    WorkflowState.READY: {WorkflowState.QUESTION_GENERATION, WorkflowState.FAILED},
    WorkflowState.QUESTION_GENERATION: {WorkflowState.WAITING_FOR_ANSWER, WorkflowState.FAILED},
    WorkflowState.WAITING_FOR_ANSWER: {WorkflowState.ANSWER_EVALUATION, WorkflowState.FAILED},
    WorkflowState.ANSWER_EVALUATION: {WorkflowState.NEXT_QUESTION, WorkflowState.ROUND_COMPLETE, WorkflowState.FAILED},
    WorkflowState.NEXT_QUESTION: {WorkflowState.QUESTION_GENERATION, WorkflowState.ROUND_COMPLETE, WorkflowState.FAILED},
    WorkflowState.ROUND_COMPLETE: {WorkflowState.NEXT_ROUND, WorkflowState.INTERVIEW_COMPLETED, WorkflowState.FAILED},
    WorkflowState.NEXT_ROUND: {WorkflowState.QUESTION_GENERATION, WorkflowState.FAILED},
    WorkflowState.INTERVIEW_COMPLETED: {WorkflowState.REPORT_GENERATION, WorkflowState.FAILED},
    WorkflowState.REPORT_GENERATION: {WorkflowState.COMPLETED, WorkflowState.FAILED},
    WorkflowState.COMPLETED: set(),
    WorkflowState.FAILED: set(),
}

IMMUTABLE_KEYS = {
    "interview_id",
    "user_id",
    "raw_resume_file_path",
    "raw_jd_file_path",
    "resume_raw_text",
    "jd_raw_text",
}


class SupervisorAgent:
    """
    Deterministic Supervisor Agent for InterviewSage AI.
    Controls graph routing, lifecycle state machine, prerequisite enforcement, and error recovery.
    """

    def __init__(self, max_retries: int = MAX_RETRIES) -> None:
        self.max_retries = max_retries

    def validate_transition(self, current_state: str, next_state: str) -> bool:
        """Verify whether moving from current_state to next_state is valid."""
        try:
            curr = WorkflowState(current_state)
            nxt = WorkflowState(next_state)
            return nxt in ALLOWED_TRANSITIONS.get(curr, set())
        except ValueError:
            logger.warning(f"[Supervisor] Unknown workflow state transition: {current_state} -> {next_state}")
            return False

    def validate_prerequisites(self, target_state: str, state: InterviewState) -> Tuple[bool, Optional[str]]:
        """Validate whether state contains all required data before transitioning to target_state."""
        try:
            target = WorkflowState(target_state)
        except ValueError:
            return False, f"Invalid target state: {target_state}"

        if target == WorkflowState.RESUME_ANALYSIS:
            if not state.get("resume_raw_text"):
                return False, "Missing resume_raw_text in state"

        elif target == WorkflowState.JD_ANALYSIS:
            if not state.get("jd_raw_text"):
                return False, "Missing jd_raw_text in state"

        elif target == WorkflowState.INTERVIEW_PLANNING:
            if not state.get("resume_data") and not state.get("resume_json"):
                return False, "Missing resume_data for interview planning"

        elif target == WorkflowState.QUESTION_GENERATION:
            if not state.get("interview_plan"):
                return False, "Missing interview_plan for question generation"

        elif target == WorkflowState.ANSWER_EVALUATION:
            if not state.get("answers"):
                return False, "Missing answers array for answer evaluation"
            if not state.get("current_question"):
                return False, "Missing current_question for answer evaluation"

        elif target == WorkflowState.REPORT_GENERATION:
            if not state.get("evaluations"):
                return False, "Missing evaluations array for report generation"

        return True, None

    def decide_next_step(self, state: InterviewState) -> str:
        """
        Deterministic state router. Given current InterviewState, computes the next graph node name.
        """
        stage_str = state.get("workflow_stage", "INITIALIZING")
        try:
            current_stage = WorkflowState(stage_str)
        except ValueError:
            logger.error(f"[Supervisor] Unknown stage '{stage_str}'; routing to FAILED")
            return "FAILED"

        # 1. INITIALIZING -> RESUME_ANALYSIS
        if current_stage == WorkflowState.INITIALIZING:
            valid, err = self.validate_prerequisites(WorkflowState.RESUME_ANALYSIS.value, state)
            if valid:
                return "resume_agent"
            logger.warning(f"[Supervisor] Prerequisite failed for RESUME_ANALYSIS: {err}")
            return "FAILED"

        # 2. RESUME_ANALYSIS -> JD_ANALYSIS
        if current_stage == WorkflowState.RESUME_ANALYSIS:
            if state.get("resume_data"):
                return "jd_agent"
            return "resume_agent"

        # 3. JD_ANALYSIS -> INTERVIEW_PLANNING
        if current_stage == WorkflowState.JD_ANALYSIS:
            if state.get("jd_data"):
                return "interview_planner_agent"
            return "jd_agent"

        # 4. INTERVIEW_PLANNING -> QUESTION_GENERATION
        if current_stage == WorkflowState.INTERVIEW_PLANNING:
            if state.get("interview_plan"):
                current_round = state.get("current_round", "TECHNICAL")
                return "question_generator_hr" if current_round == "HR" else "question_generator_tech"
            return "interview_planner_agent"

        # 5. QUESTION_GENERATION / READY -> WAITING_FOR_ANSWER / EVALUATION
        if current_stage in (WorkflowState.READY, WorkflowState.QUESTION_GENERATION):
            if state.get("current_question"):
                return "WAIT"  # Graph pauses for candidate answer submission

        # 6. WAITING_FOR_ANSWER -> ANSWER_EVALUATION
        if current_stage == WorkflowState.WAITING_FOR_ANSWER:
            current_round = state.get("current_round", "TECHNICAL")
            return "evaluation_agent_hr" if current_round == "HR" else "evaluation_agent_tech"

        # 7. ANSWER_EVALUATION -> NEXT_QUESTION or ROUND_COMPLETE
        if current_stage == WorkflowState.ANSWER_EVALUATION:
            plan = state.get("interview_plan") or {}
            current_round = state.get("current_round", "TECHNICAL")
            
            target_count = (
                plan.get("hr_question_count", 1)
                if current_round == "HR"
                else plan.get("technical_question_count", plan.get("total_questions", 5))
            )
            
            asked_count = len(state.get("questions_asked") or [])
            if asked_count < target_count:
                return "question_generator_hr" if current_round == "HR" else "question_generator_tech"
            return "report_generator_agent"

        # 8. INTERVIEW_COMPLETED / REPORT_GENERATION -> END
        if current_stage == WorkflowState.REPORT_GENERATION:
            if state.get("final_report"):
                return "COMPLETED"
            return "report_generator_agent"

        if current_stage in (WorkflowState.COMPLETED, WorkflowState.FAILED):
            return current_stage.value

        return "FAILED"

    def handle_failure(self, state: InterviewState, error: AgentError) -> dict:
        """
        Handle an agent or workflow error deterministically.
        Increments retry count, logs error, and transitions to FAILED if retry limit exceeded.
        """
        retries = state.get("retry_count_this_node", 0) + 1
        error_log = list(state.get("error_log") or [])
        error_log.append({
            "agent": error.agent_name,
            "code": error.code.value if hasattr(error.code, "value") else str(error.code),
            "message": error.message,
            "retry_count": retries,
        })

        if retries > self.max_retries or not error.retryable:
            logger.error(f"[Supervisor] Agent {error.agent_name} failed permanently: {error.message}")
            return {
                "workflow_stage": WorkflowState.FAILED.value,
                "error_log": error_log,
                "retry_count_this_node": retries,
            }

        logger.warning(f"[Supervisor] Agent {error.agent_name} retry {retries}/{self.max_retries}: {error.message}")
        return {
            "error_log": error_log,
            "retry_count_this_node": retries,
        }

    def protect_immutable_context(self, original_state: InterviewState, updates: dict) -> dict:
        """
        Sanitize state updates to guarantee agents never overwrite immutable context fields.
        """
        sanitized = dict(updates)
        for key in IMMUTABLE_KEYS:
            if key in sanitized and sanitized[key] != original_state.get(key):
                logger.warning(f"[Supervisor] Blocked attempt to mutate immutable key '{key}'")
                del sanitized[key]
        return sanitized
