"""
Canonical Agent Contracts & Pydantic Schemas for InterviewSage AI (Phase 4B).
Defines typed boundary contracts for Multi-Agent input/output and shared context.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
import uuid

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
    details: Optional[Dict[str, Any]] = None


class AgentResult(BaseModel, Generic[T]):
    success: bool
    agent_name: str
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data: Optional[T] = None
    error: Optional[AgentError] = None
    execution_time_ms: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Sub-Entities ───────────────────────────────────────────────

class ExperienceEntry(BaseModel):
    id: Optional[str] = None
    title: str = ""
    company: str = ""
    period: str = ""
    description: str = ""
    highlights: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    id: Optional[str] = None
    degree: str = ""
    institution: str = ""
    field_of_study: str = ""
    graduation_year: str = ""
    gpa: Optional[str] = None


class ProjectEntry(BaseModel):
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    technologies: List[str] = Field(default_factory=list)
    link: Optional[str] = None
    role: Optional[str] = None


class CertificationEntry(BaseModel):
    id: Optional[str] = None
    name: str = ""
    issuer: str = ""
    issue_date: str = ""


# ── ResumeAgent Contracts ──────────────────────────────────────

class ResumeAgentInput(BaseModel):
    resume_raw_text: str = Field(..., min_length=1, description="Extracted raw text from resume PDF")
    candidate_id: Optional[str] = None
    file_name: Optional[str] = None


class ResumeAnalysis(BaseModel):
    summary: str = Field(default="", description="Executive candidate summary extracted from resume")
    technical_skills: List[str] = Field(default_factory=list, description="Technical skills and technologies")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills and domain competencies")
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    career_level: str = Field(default="MID", description="Seniority signal: JUNIOR, MID, SENIOR, STAFF, UNKNOWN")
    resume_quality_score: int = Field(default=85, ge=0, le=100)

    @field_validator("career_level")
    @classmethod
    def validate_seniority(cls, v: str) -> str:
        allowed = {"JUNIOR", "MID", "SENIOR", "STAFF", "UNKNOWN"}
        return v.upper() if v.upper() in allowed else "MID"


# ── JDAgent Contracts ──────────────────────────────────────────

class JDAnalysisInput(BaseModel):
    jd_raw_text: str = Field(..., min_length=1, description="Raw job description text")
    job_title: Optional[str] = None


class JDAnalysis(BaseModel):
    target_role: str = Field(default="Software Engineer", description="Target role title")
    seniority_required: str = Field(default="MID", description="Required seniority: JUNIOR, MID, SENIOR, STAFF")
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    core_responsibilities: List[str] = Field(default_factory=list)
    domain_knowledge: List[str] = Field(default_factory=list)

    @field_validator("seniority_required")
    @classmethod
    def validate_seniority(cls, v: str) -> str:
        allowed = {"JUNIOR", "MID", "SENIOR", "STAFF", "FRESHER"}
        return v.upper() if v.upper() in allowed else "MID"


# ── InterviewPlannerAgent Contracts ───────────────────────────

class InterviewPlanInput(BaseModel):
    seniority_signal: str = Field(default="MID")
    interview_type: str = Field(default="HYBRID")
    resume_skills: List[str] = Field(default_factory=list)
    required_jd_skills: List[str] = Field(default_factory=list)


class CompetencyWeight(BaseModel):
    name: str
    weight: int = Field(default=10, ge=1, le=100)
    category: str = "TECHNICAL"


class InterviewPlan(BaseModel):
    seniority_tier: str = "MID"
    total_questions: int = Field(default=5, ge=1, le=20)
    hr_question_count: int = Field(default=2, ge=0)
    technical_question_count: int = Field(default=3, ge=0)
    competencies: List[CompetencyWeight] = Field(default_factory=list)
    difficulty_progression: List[str] = Field(default_factory=list)


# ── QuestionGeneratorAgent Contracts ─────────────────────────

class QuestionGenerationInput(BaseModel):
    interview_id: str
    current_round: str = "TECHNICAL"
    competency_targeted: str = "General"
    difficulty: str = "MEDIUM"
    question_type: str = "fundamentals"
    candidate_skills: List[str] = Field(default_factory=list)
    previous_questions_text: List[str] = Field(default_factory=list)


class GeneratedQuestion(BaseModel):
    question_text: str
    competency_targeted: str
    difficulty: str = "MEDIUM"
    question_type: str = "fundamentals"
    personalisation_note: str = ""
    expected_answer: Optional[str] = None
    evaluation_rubric: List[str] = Field(default_factory=list)

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
    expected_rubric: Optional[List[str]] = None


class AnswerEvaluation(BaseModel):
    score: int = Field(..., ge=1, le=10, description="Overall score on 1–10 scale")
    rubric_breakdown: Dict[str, int] = Field(default_factory=dict, description="Sub-scores 1–5 per dimension")
    feedback: str = Field(default="", description="Detailed qualitative feedback")
    ideal_answer_summary: str = Field(default="", description="Ideal reference summary")
    needs_human_review: bool = Field(default=False)
    technical_score: float = Field(default=0.0)
    communication_score: float = Field(default=0.0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def sub_scores_in_range(self) -> "AnswerEvaluation":
        for dim, val in self.rubric_breakdown.items():
            if not (1 <= val <= 5):
                raise ValueError(f"Sub-score for '{dim}' is {val} — must be 1–5.")
        return self


# ── ReportAgent Contracts ─────────────────────────────────────

class ReportGenerationInput(BaseModel):
    interview_id: str
    candidate_id: str
    evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    total_questions: int = 5


class InterviewReport(BaseModel):
    overall_score: int = Field(default=75, ge=0, le=100)
    technical_score: int = Field(default=75, ge=0, le=100)
    communication_score: int = Field(default=75, ge=0, le=100)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    skill_gaps: List[str] = Field(default_factory=list)
    recommendation: str = Field(default="PASS")
    improvement_roadmap: List[str] = Field(default_factory=list)


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
    resume_id: Optional[str] = None
    jd_id: Optional[str] = None
    raw_resume_text: str = ""
    raw_jd_text: str = ""

    # 2. RUNTIME WORKFLOW STATE
    current_round: str = "TECHNICAL"
    current_question_index: int = 1
    total_questions: int = 3
    status: str = "PLANNING"

    # 3. GENERATED AGENT ARTIFACTS
    resume_analysis: Optional[ResumeAnalysis] = None
    jd_analysis: Optional[JDAnalysis] = None
    interview_plan: Optional[InterviewPlan] = None
    current_question: Optional[GeneratedQuestion] = None

    # 4. EVALUATION & ACCUMULATED DATA
    questions_asked: List[Dict[str, Any]] = Field(default_factory=list)
    answers_submitted: List[Dict[str, Any]] = Field(default_factory=list)
    evaluations: List[AnswerEvaluation] = Field(default_factory=list)
    final_report: Optional[InterviewReport] = None
