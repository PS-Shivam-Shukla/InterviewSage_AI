from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InterviewCreateRequest(BaseModel):
    resume_id: str | None = Field(None, description="Resume identifier")
    jd_id: str | None = Field(None, description="Job description identifier")
    role: str | None = Field(None, description="Target role title")
    experience_level: str | None = Field(None, description="Candidate experience level (e.g. Fresher, Mid, Senior)")
    skills: list[str] | None = Field(default_factory=list, description="Target technical skills")
    rounds: list[str] | None = Field(default_factory=list, description="Selected interview rounds")
    difficulty: str | None = Field("Standard", description="Rigor difficulty")


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(..., description="Answer to the current interview prompt")
    question_id: str | None = Field(None, description="Current question ID")
    question_text: str | None = Field(None, description="Current question text")


class BlueprintApprovalRequest(BaseModel):
    approved: bool = Field(True, description="Recruiter approval decision")
    overrides: dict[str, Any] | None = Field(default_factory=dict, description="Custom blueprint overrides")


class BlueprintApprovalResponse(BaseModel):
    interview_id: str
    status: str
    message: str
    overrides_applied: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class InterviewStatusResponse(BaseModel):
    id: str
    status: str
    target_role: str | None = None
    target_company: str | None = None
    current_round: str | None
    overall_score: int | None
    started_at: datetime
    completed_at: datetime | None
    total_questions: int | None = 5

    model_config = ConfigDict(from_attributes=True)


class InterviewPlanResponse(BaseModel):
    interview_id: str
    plan: dict[str, object]

    model_config = ConfigDict(from_attributes=True)


class InterviewAnswerResponse(BaseModel):
    interview_id: str
    message: str
    status: str | None = "IN_PROGRESS"
    evaluation: dict[str, Any] | None = None
    next_question: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)
