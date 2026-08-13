"""
Resume Agent (Section 10.2)
Converts raw resume text → structured ResumeAnalysis via LLM execution.
Evaluates resume_quality_score (formatting, section completeness, clarity, technical depth).
No ATS score (ATS score requires a Job Description in Sprint 0.3).
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.prompts.loader import get_system_prompt, get_developer_prompt


# ── Output schema ─────────────────────────────────────────────

class ExperienceEntry(BaseModel):
    id: Optional[str] = None
    title: str = ""
    company: str = ""
    period: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    employment_type: str = ""
    description: str = ""
    highlights: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    ownership_bullets: List[str] = Field(default_factory=list, description="Factual evidence of independent feature or service ownership")
    architecture_bullets: List[str] = Field(default_factory=list, description="Factual evidence of system design, database architecture, or microservice design")
    leadership_bullets: List[str] = Field(default_factory=list, description="Factual evidence of mentoring, code reviews, or team leadership")
    complexity_bullets: List[str] = Field(default_factory=list, description="Factual evidence of high scale, performance optimization, or complex technical delivery")


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


class ResumeAnalysis(BaseModel):
    summary: str = Field(default="", description="Executive candidate summary extracted from resume")
    technical_skills: List[str] = Field(default_factory=list, description="All technical skills and technologies")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills, domain competencies, and leadership qualities")
    experience: List[ExperienceEntry] = Field(default_factory=list, description="List of work experience entries")
    education: List[EducationEntry] = Field(default_factory=list, description="List of education and academic credentials")
    projects: List[ProjectEntry] = Field(default_factory=list, description="List of key projects")
    certifications: List[CertificationEntry] = Field(default_factory=list, description="List of certifications")
    languages: List[str] = Field(default_factory=list, description="Spoken/written human languages")
    strengths: List[str] = Field(default_factory=list, description="Key candidate strengths identified")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for candidate improvement")
    career_level: Optional[str] = Field(default="UNKNOWN", description="Deprecated. Final seniority is computed deterministically by SeniorityEngine in Python.")
    resume_quality_score: int = Field(default=85, ge=0, le=100, description="Calculated resume formatting, clarity, section completeness, and technical depth score (0 to 100)")


# ── Agent ─────────────────────────────────────────────────────

class ResumeAgent(BaseAgent):
    agent_name = "ResumeAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.1   # deterministic extraction

    def _run(self, state: InterviewState, retry_feedback: Optional[str] = None) -> dict:
        raw_text = state.get("resume_raw_text", "")
        if not raw_text:
            raise ValueError("resume_raw_text is missing from state")

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("resume_agent", self.prompt_version),
            developer_prompt=get_developer_prompt("resume_agent", self.prompt_version),
            user_content=f"Resume Raw Text:\n{raw_text}",
        )

        analysis: ResumeAnalysis = self._invoke_structured(messages, ResumeAnalysis, retry_feedback)

        return {"resume_data": analysis.model_dump()}

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        return {
            "resume_data": ResumeAnalysis().model_dump(),
            "error_log": [{"agent": self.agent_name, "error": error}],
        }
