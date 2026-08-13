from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class JobDescriptionCreateRequest(BaseModel):
    raw_text: str = Field(..., description="Full job description text")
    target_role: str = Field(..., description="Target role for this job description")
    company_name: Optional[str] = Field(None, description="Optional company name")
    industry: Optional[str] = Field(None, description="Optional industry")


class JobDescriptionResponse(BaseModel):
    id: str
    user_id: str
    raw_text: str
    target_role: str
    company_name: Optional[str]
    industry: Optional[str]
    required_skills: List[str]
    seniority_level: str
    status: str = "PROCESSING"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionMatchResponse(BaseModel):
    jd_id: str
    resume_id: str
    target_role: str
    company_name: Optional[str] = None
    candidate_seniority: str
    required_seniority: str
    ats_score: int = Field(..., description="Keyword & skill match percentage (0-100)")
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    resume_skill_count: int
    jd_skill_count: int

    model_config = ConfigDict(from_attributes=True)
