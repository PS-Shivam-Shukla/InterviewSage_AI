"""
InterviewState / GraphState — the single shared, serialisable state object that flows
through every LangGraph node (Section 7 of the master spec).

Design rules:
- Every field that is written by an agent is listed here with its owner.
- Agents return ONLY the keys they modify (reducer pattern).
- Transient fields (retry_count_this_node, error_log) are included here
  but are not persisted to SQL tables; they live only in the checkpoint.
- All JSON-serialisable types — no SQLAlchemy models inside state.
"""

from __future__ import annotations

from typing import Annotated, Any, Optional
from typing_extensions import TypedDict
import operator


def _append(existing: list | None, new: list | None) -> list:
    """Reducer: append new items to an existing list."""
    res = list(existing) if existing is not None else []
    if new:
        res.extend(new)
    return res


class InterviewState(TypedDict, total=False):
    """
    Shared state for the interview LangGraph workflow.

    Convention:
        total=False  → all keys are optional at state creation time,
                       but agents must check for None before using them.
    """

    # ── Identity ──────────────────────────────────────────────
    interview_id: str                   # Primary key; thread_id for LangGraph checkpointer
    user_id: str                        # Owning user

    # ── Raw inputs (written at graph start, read by extraction agents) ─
    raw_resume_file_path: str           # Path to resume file
    raw_jd_file_path: str               # Path to job description file
    resume_raw_text: str                # Raw text extracted from resume file
    jd_raw_text: str                    # Raw job description text
    pending_answer: str                 # Candidate's answer for the current turn
    document_confidence_score: float    # Ingestion confidence score

    # ── Agent & Engine outputs (set once, read by downstream nodes) ───
    resume_data: dict[str, Any]         # Written by: ResumeAgent
    jd_data: dict[str, Any]             # Written by: JDAgent
    resume_json: dict[str, Any]         # Standardized Resume JSON
    jd_json: dict[str, Any]             # Standardized JD JSON
    ats_analysis: dict[str, Any]        # Written by: ATSAgent
    ats_result: dict[str, Any]          # ATS Evaluation Result
    profile_summary: dict[str, Any]     # Written by: ProfileIntelligenceAgent
    competency_matrix: list[dict]       # Written by: CompetencyMappingAgent
    skill_graph: dict[str, Any]         # Normalized Skill Graph
    capability_graph: dict[str, Any]    # Candidate Capability Graph

    # ── DISE Strategy & Blueprint Engine ────────────────────────
    classification: dict[str, Any]      # Written by: CandidateClassifier Node
    interview_strategy: dict[str, Any]  # Written by: Strategy Agent
    interview_blueprint: dict[str, Any] # Written by: Blueprint Generator Node
    interview_plan: dict[str, Any]      # Written by: InterviewPlannerAgent

    # ── Runtime interview progress ────────────────────────────
    current_round: str                  # "HR" | "TECHNICAL" | "COMPLETE"
    current_question: Optional[dict]    # Written by: Question Personalization Node; None between turns
    questions_asked: Annotated[list[dict], _append]  # Accumulates across all turns
    answers: Annotated[list[dict], _append]          # Accumulates candidate answers
    evaluations: Annotated[list[dict], _append]      # Accumulates per-answer evaluations

    # ── Post-interview ────────────────────────────────────────
    coaching_plan: dict[str, Any]       # Written by: CareerCoachAgent
    learning_plan: dict[str, Any]       # Generated learning recommendations
    final_report: Optional[dict]        # Written by: ReportGeneratorAgent

    # ── Orchestration / transient / HITL ──────────────────────
    workflow_stage: str                 # Current execution stage
    human_review_required: bool         # HITL Interrupt Gate Flag
    retry_count_this_node: int          # Reset on each node entry by LangGraph runtime
    error_log: Annotated[list[dict], _append]  # Any agent can append errors here
    next_node: Optional[str]            # Supervisor routing decision

    # ── Model-Mediated Policy & Verification ───────────────────
    policy_iteration_count: int         # Tracks bounded PolicyNode loop iterations (max 5)
    policy_decisions: Annotated[list[dict], _append]  # Log of tool_call and finish decisions
    observations: Annotated[list[dict], _append]      # Log of tool execution observations
    available_tools: list[dict]         # Machine-readable MCP tool schemas exposed to LLM
    verification_report: dict[str, Any] # Written by: ReportVerificationNode


# V4 Architecture Alias
GraphState = InterviewState
