from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ResumeResponse(BaseModel):
    id: str
    user_id: str
    file_path: str
    raw_text: str
    parsed_skills: List[str]
    parsed_experience: List[Any]
    seniority_signal: str
    status: str = "PROCESSING"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillBreakdown(BaseModel):
    technical: List[str]
    soft: List[str]
    missing: List[str]
    all: List[str]


class ExperienceItem(BaseModel):
    id: str
    title: str
    company: str
    period: str
    description: str
    highlights: List[str]
    technologies: List[str]


class EducationItem(BaseModel):
    id: str
    degree: str
    institution: str
    field_of_study: str
    graduation_year: str
    gpa: Optional[str] = None


class ProjectItem(BaseModel):
    id: str
    title: str
    description: str
    technologies: List[str]
    link: Optional[str] = None
    role: Optional[str] = None


class CertificationItem(BaseModel):
    id: str
    name: str
    issuer: str
    issue_date: str


class ResumeAnalysisResponse(BaseModel):
    resume_id: str
    file_name: str
    status: Optional[str] = "COMPLETED"
    resume_quality_score: int
    seniority_signal: str
    seniority_score: Optional[int] = 0
    experience_metrics: Optional[Dict[str, int]] = None
    seniority_breakdown: Optional[Dict[str, int]] = None
    seniority_evidence: Optional[List[str]] = Field(default_factory=list)
    seniority_limitations: Optional[List[str]] = Field(default_factory=list)
    skills: SkillBreakdown
    experience: List[ExperienceItem]
    education: List[EducationItem]
    projects: List[ProjectItem]
    certifications: List[CertificationItem]
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    section_completeness: Dict[str, int]
