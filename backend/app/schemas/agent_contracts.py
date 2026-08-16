"""
Canonical Agent Contracts & Pydantic Schemas for InterviewSage AI (Phase 4B).
Defines typed boundary contracts for Multi-Agent input/output and shared context.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

T = TypeVar("T")


# ── Error & Result Envelope ────────────────────────────────────


class AgentErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_MALFORMED_OUTPUT = "LLM_MALFORMED_OUTPUT"
    TOOL_MCP_FAILURE = "TOOL_MCP_FAILURE"
    DATABASE_FAILURE = "DATABASE_FAILURE"
    MISSING_REQUIRED_CONTEXT = "MISSING_REQUIRED_CONTEXT"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    UNEXPECTED_FAILURE = "UNEXPECTED_FAILURE"


class AgentError(BaseModel):
    code: AgentErrorCode
    message: str
    retryable: bool = True
    agent_name: str
    details: dict[str, Any] | None = None


class AgentResult(BaseModel, Generic[T]):
    success: bool
    agent_name: str
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data: T | None = None
    error: AgentError | None = None
    execution_time_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# ── Sub-Entities ───────────────────────────────────────────────


class ExperienceEntry(BaseModel):
    id: str | None = None
    title: str = ""
    company: str = ""
    period: str = ""
    description: str = ""
    highlights: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    id: str | None = None
    degree: str = ""
    institution: str = ""
    field_of_study: str = ""
    graduation_year: str = ""
    gpa: str | None = None


class ProjectEntry(BaseModel):
    id: str | None = None
    title: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    link: str | None = None
    role: str | None = None


class CertificationEntry(BaseModel):
    id: str | None = None
    name: str = ""
    issuer: str = ""
    issue_date: str = ""


# ── ResumeAgent Contracts ──────────────────────────────────────


class ResumeAgentInput(BaseModel):
    resume_raw_text: str = Field(
        ..., min_length=1, description="Extracted raw text from resume PDF"
    )
    candidate_id: str | None = None
    file_name: str | None = None


from app.agents.resume_agent import ResumeAnalysis


# ── JDAgent Contracts ──────────────────────────────────────────


class JDAnalysisInput(BaseModel):
    jd_raw_text: str = Field(..., min_length=1, description="Raw job description text")
    job_title: str | None = None


class JDAnalysis(BaseModel):
    target_role: str = Field(default="Software Engineer", description="Target role title")
    seniority_required: str = Field(
        default="MID", description="Required seniority: JUNIOR, MID, SENIOR, STAFF"
    )
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    core_responsibilities: list[str] = Field(default_factory=list)
    domain_knowledge: list[str] = Field(default_factory=list)

    @field_validator("seniority_required")
    @classmethod
    def validate_seniority(cls, v: str) -> str:
        allowed = {"JUNIOR", "MID", "SENIOR", "STAFF", "FRESHER"}
        return v.upper() if v.upper() in allowed else "MID"


# ── InterviewPlannerAgent Contracts ───────────────────────────


class InterviewPlanInput(BaseModel):
    seniority_signal: str = Field(default="MID")
    interview_type: str = Field(default="HYBRID")
    resume_skills: list[str] = Field(default_factory=list)
    required_jd_skills: list[str] = Field(default_factory=list)


class CompetencyWeight(BaseModel):
    name: str
    weight: int = Field(default=10, ge=1, le=100)
    category: str = "TECHNICAL"


class InterviewPlan(BaseModel):
    seniority_tier: str = "MID"
    total_questions: int = Field(default=5, ge=1, le=20)
    hr_question_count: int = Field(default=2, ge=0)
    technical_question_count: int = Field(default=3, ge=0)
    competencies: list[CompetencyWeight] = Field(default_factory=list)
    difficulty_progression: list[str] = Field(default_factory=list)


# ── QuestionGeneratorAgent Contracts ─────────────────────────


class QuestionGenerationInput(BaseModel):
    interview_id: str
    current_round: str = "TECHNICAL"
    competency_targeted: str = "General"
    difficulty: str = "MEDIUM"
    question_type: str = "fundamentals"
    candidate_skills: list[str] = Field(default_factory=list)
    previous_questions_text: list[str] = Field(default_factory=list)


class GeneratedQuestion(BaseModel):
    question_text: str
    competency_targeted: str
    difficulty: str = "MEDIUM"
    question_type: str = "fundamentals"
    personalisation_note: str = ""
    expected_answer: str | None = None
    evaluation_rubric: list[str] = Field(default_factory=list)

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        return v.upper() if v.upper() in {"EASY", "MEDIUM", "HARD", "ADVANCED"} else "MEDIUM"


# ── EvaluationAgent Contracts ─────────────────────────────────


class AnswerEvaluationInput(BaseModel):
    question_text: str
    candidate_answer: str
    competency_targeted: str = "General"
    question_type: str = "fundamentals"
    seniority: str = "MID"
    expected_rubric: list[str] | None = None


class AnswerEvaluation(BaseModel):
    score: int = Field(..., ge=1, le=10, description="Overall score on 1–10 scale")
    rubric_breakdown: dict[str, int] = Field(
        default_factory=dict, description="Sub-scores 1–5 per dimension"
    )
    feedback: str = Field(default="", description="Detailed qualitative feedback")
    ideal_answer_summary: str = Field(default="", description="Ideal reference summary")
    needs_human_review: bool = Field(default=False)
    technical_score: float = Field(default=0.0)
    communication_score: float = Field(default=0.0)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def sub_scores_in_range(self) -> AnswerEvaluation:
        for dim, val in self.rubric_breakdown.items():
            if not (1 <= val <= 5):
                raise ValueError(f"Sub-score for '{dim}' is {val} — must be 1–5.")
        return self


# ── ReportAgent Contracts ─────────────────────────────────────


class ReportGenerationInput(BaseModel):
    interview_id: str
    candidate_id: str
    evaluations: list[dict[str, Any]] = Field(default_factory=list)
    total_questions: int = 5


class InterviewReport(BaseModel):
    overall_score: int = Field(default=75, ge=0, le=100)
    technical_score: int = Field(default=75, ge=0, le=100)
    communication_score: int = Field(default=75, ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    recommendation: str = Field(default="PASS")
    improvement_roadmap: list[str] = Field(default_factory=list)


# ── Shared Interview Context ──────────────────────────────────


class InterviewContext(BaseModel):
    """
    Unified, strongly typed context encapsulating the complete interview state.

    Data Ownership & Mutability Rules:
    - IMMUTABLE DATA: Source files and identities (never mutated by agents).
    - RUNTIME STATE: Active round, step index, progress state.
    - GENERATED DATA: Structural artifacts generated by Specialist Agents.
    - EVALUATION DATA: Accumulation of candidate turns and scores.
    """

    # 1. IMMUTABLE SOURCE DATA
    interview_id: str
    candidate_id: str
    resume_id: str | None = None
    jd_id: str | None = None
    raw_resume_text: str = ""
    raw_jd_text: str = ""

    # 2. RUNTIME WORKFLOW STATE
    current_round: str = "TECHNICAL"
    current_question_index: int = 1
    total_questions: int = 3
    status: str = "PLANNING"

    # 3. GENERATED AGENT ARTIFACTS
    resume_analysis: ResumeAnalysis | None = None
    jd_analysis: JDAnalysis | None = None
    interview_plan: InterviewPlan | None = None
    current_question: GeneratedQuestion | None = None

    # 4. EVALUATION & ACCUMULATED DATA
    questions_asked: list[dict[str, Any]] = Field(default_factory=list)
    answers_submitted: list[dict[str, Any]] = Field(default_factory=list)
    evaluations: list[AnswerEvaluation] = Field(default_factory=list)
    final_report: InterviewReport | None = None
