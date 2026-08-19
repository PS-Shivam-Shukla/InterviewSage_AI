from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeResponse(BaseModel):
    id: str
    user_id: str
    file_path: str
    raw_text: str
    parsed_skills: list[str]
    parsed_experience: list[Any]
    seniority_signal: str
    status: str = "PROCESSING"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillBreakdown(BaseModel):
    technical: list[str]
    soft: list[str]
    missing: list[str]
    all: list[str]


class ExperienceItem(BaseModel):
    id: str
    title: str
    company: str
    period: str
    description: str
    highlights: list[str]
    technologies: list[str]


class EducationItem(BaseModel):
    id: str
    degree: str
    institution: str
    field_of_study: str
    graduation_year: str
    gpa: str | None = None


class ProjectItem(BaseModel):
    id: str
    title: str
    description: str
    technologies: list[str]
    link: str | None = None
    role: str | None = None


class CertificationItem(BaseModel):
    id: str
    name: str = ""
    issuer: str = ""
    issue_date: str | None = ""


class ResumeAnalysisResponse(BaseModel):
    resume_id: str
    file_name: str
    status: str | None = "COMPLETED"
    resume_quality_score: int = 85
    seniority_signal: str = "MID"
    seniority_score: int | None = 0
    experience_metrics: dict[str, int] | None = None
    seniority_breakdown: dict[str, int] | None = None
    seniority_evidence: list[str] | None = Field(default_factory=list)
    seniority_limitations: list[str] | None = Field(default_factory=list)
    skills: SkillBreakdown
    experience: list[ExperienceItem]
    education: list[EducationItem]
    projects: list[ProjectItem]
    certifications: list[CertificationItem]
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    section_completeness: dict[str, int]
