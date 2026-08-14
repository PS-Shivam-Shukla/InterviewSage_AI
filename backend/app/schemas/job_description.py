from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobDescriptionCreateRequest(BaseModel):
    raw_text: str = Field(..., description="Full job description text")
    target_role: str = Field(..., description="Target role for this job description")
    company_name: str | None = Field(None, description="Optional company name")
    industry: str | None = Field(None, description="Optional industry")


class JobDescriptionResponse(BaseModel):
    id: str
    user_id: str
    raw_text: str
    target_role: str
    company_name: str | None
    industry: str | None
    required_skills: list[str]
    seniority_level: str
    status: str = "PROCESSING"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionMatchResponse(BaseModel):
    jd_id: str
    resume_id: str
    target_role: str
    company_name: str | None = None
    candidate_seniority: str
    required_seniority: str
    ats_score: int = Field(..., description="Keyword & skill match percentage (0-100)")
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    resume_skill_count: int
    jd_skill_count: int

    model_config = ConfigDict(from_attributes=True)
