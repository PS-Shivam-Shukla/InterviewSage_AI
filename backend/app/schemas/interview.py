from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, ConfigDict


class InterviewCreateRequest(BaseModel):
    resume_id: Optional[str] = Field(None, description="Resume identifier")
    jd_id: Optional[str] = Field(None, description="Job description identifier")
    role: Optional[str] = Field(None, description="Target role title")
    experience_level: Optional[str] = Field(None, description="Candidate experience level (e.g. Fresher, Mid, Senior)")
    skills: Optional[List[str]] = Field(default_factory=list, description="Target technical skills")
    rounds: Optional[List[str]] = Field(default_factory=list, description="Selected interview rounds")
    difficulty: Optional[str] = Field("Standard", description="Rigor difficulty")


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(..., description="Answer to the current interview prompt")
    question_id: Optional[str] = Field(None, description="Current question ID")
    question_text: Optional[str] = Field(None, description="Current question text")


class BlueprintApprovalRequest(BaseModel):
    approved: bool = Field(True, description="Recruiter approval decision")
    overrides: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom blueprint overrides")


class BlueprintApprovalResponse(BaseModel):
    interview_id: str
    status: str
    message: str
    overrides_applied: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class InterviewStatusResponse(BaseModel):
    id: str
    status: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    current_round: str | None
    overall_score: int | None
    started_at: datetime
    completed_at: datetime | None
    total_questions: Optional[int] = 5

    model_config = ConfigDict(from_attributes=True)


class InterviewPlanResponse(BaseModel):
    interview_id: str
    plan: dict[str, object]

    model_config = ConfigDict(from_attributes=True)


class InterviewAnswerResponse(BaseModel):
    interview_id: str
    message: str
    status: Optional[str] = "IN_PROGRESS"
    evaluation: Optional[Dict[str, Any]] = None
    next_question: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
