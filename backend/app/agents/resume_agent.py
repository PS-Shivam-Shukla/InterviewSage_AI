"""
Resume Agent (Section 10.2)
Converts raw resume text → structured ResumeAnalysis via LLM execution.
Evaluates resume_quality_score (formatting, section completeness, clarity, technical depth).
No ATS score (ATS score requires a Job Description in Sprint 0.3).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.prompts.loader import get_developer_prompt, get_system_prompt

# ── Output schema ─────────────────────────────────────────────


class ExperienceEntry(BaseModel):
    id: str | None = None
    title: str | None = None
    company: str | None = None
    period: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    employment_type: str | None = None
    description: str | None = None
    highlights: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    ownership_bullets: list[str] = Field(
        default_factory=list,
        description="Factual evidence of independent feature or service ownership",
    )
    architecture_bullets: list[str] = Field(
        default_factory=list,
        description="Factual evidence of system design, database architecture, or microservice design",
    )
    leadership_bullets: list[str] = Field(
        default_factory=list,
        description="Factual evidence of mentoring, code reviews, or team leadership",
    )
    complexity_bullets: list[str] = Field(
        default_factory=list,
        description="Factual evidence of high scale, performance optimization, or complex technical delivery",
    )

    @field_validator(
        "highlights",
        "technologies",
        "ownership_bullets",
        "architecture_bullets",
        "leadership_bullets",
        "complexity_bullets",
        mode="before",
    )
    @classmethod
    def coerce_to_list(cls, v: Any) -> list:
        if isinstance(v, list):
            return v
        if isinstance(v, str) and v:
            return [v]
        return []


class EducationEntry(BaseModel):
    id: str | None = None
    degree: str | None = None
    institution: str | None = None
    field_of_study: str | None = None
    graduation_year: str | float | int | None = None
    gpa: str | float | int | None = None

    @field_validator("gpa", "graduation_year", mode="before")
    @classmethod
    def stringify_nums(cls, v: Any) -> str | None:
        if v is None:
            return None
        return str(v)


class ProjectEntry(BaseModel):
    id: str | None = None
    title: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    link: str | None = None
    role: str | None = None


class CertificationEntry(BaseModel):
    id: str | None = None
    name: str | None = ""
    issuer: str | None = ""
    issue_date: str | None = ""

    @field_validator("name", "issuer", "issue_date", mode="before")
    @classmethod
    def null_to_empty_str(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v)


class ResumeAnalysis(BaseModel):
    summary: str = Field(
        default="", description="Executive candidate summary extracted from resume"
    )
    technical_skills: list[str] = Field(
        default_factory=list, description="All technical skills and technologies"
    )
    soft_skills: list[str] = Field(
        default_factory=list,
        description="Soft skills, domain competencies, and leadership qualities",
    )

    # ── Disambiguated Experience Fields ──────────────────────────────────────
    total_experience_years: float | int | None = Field(
        default=None,
        description="Stated or estimated total years of professional experience (e.g. 5 or 5.5). Use null if omitted.",
    )
    work_experience: list[ExperienceEntry] = Field(
        default_factory=list,
        description="List of detailed work experience entries / employment history",
    )

    @property
    def experience(self) -> list[ExperienceEntry]:
        return self.work_experience

    education: list[EducationEntry] = Field(
        default_factory=list, description="List of education and academic credentials"
    )
    projects: list[ProjectEntry] = Field(default_factory=list, description="List of key projects")
    certifications: list[CertificationEntry] = Field(
        default_factory=list, description="List of certifications"
    )
    languages: list[str] = Field(default_factory=list, description="Spoken/written human languages")
    strengths: list[str] = Field(
        default_factory=list, description="Key candidate strengths identified"
    )
    weaknesses: list[str] = Field(
        default_factory=list, description="Areas for candidate improvement"
    )
    achievements: list[str] = Field(
        default_factory=list, description="Notable awards, metrics, or achievements"
    )

    @field_validator(
        "technical_skills",
        "soft_skills",
        "certifications",
        "achievements",
        mode="before",
    )
    @classmethod
    def coerce_to_list(cls, v: Any) -> list:
        if isinstance(v, list):
            return v
        if isinstance(v, str) and v:
            return [v]
        return []
    
    career_level: str | None = Field(
        default="UNKNOWN",
        description="Deprecated. Final seniority is computed deterministically by SeniorityEngine in Python.",
    )

    @field_validator("career_level", mode="before")
    @classmethod
    def validate_career_level(cls, v: str | None) -> str | None:
        if v is None:
            return "UNKNOWN"
        allowed = {"JUNIOR", "MID", "SENIOR", "STAFF", "UNKNOWN"}
        return v.upper() if v.upper() in allowed else "UNKNOWN"

    resume_quality_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Calculated resume formatting, clarity, section completeness, and technical depth score (0 to 100). Default None for zero fake metrics requirement.",
    )

    @field_validator("work_experience", mode="before")
    @classmethod
    def validate_work_experience(cls, v: Any) -> Any:
        if isinstance(v, dict):
            return [v]
        if isinstance(v, (int, float, str)):
            return []
        return v

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        data = super().model_dump(*args, **kwargs)
        if "experience" not in data or not data["experience"]:
            data["experience"] = data.get("work_experience", [])
        return data


# ── Agent ─────────────────────────────────────────────────────


class ResumeAgent(BaseAgent):
    agent_name = "ResumeAgent"
    prompt_version = "v1"
    max_retries = 1

    def _temperature(self) -> float:
        return 0.1  # deterministic extraction

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        raw_text = state.get("resume_raw_text", "")
        if not raw_text:
            raise ValueError("resume_raw_text is missing from state")

        import re
        sanitized_text = re.sub(r'[\u200b\u200c\u200d\ufeff\u00a0\u00ad]', ' ', raw_text)
        sanitized_text = re.sub(r'[ \t]+', ' ', sanitized_text)
        sanitized_text = re.sub(r'\n{3,}', '\n\n', sanitized_text).strip()
        clean_text = sanitized_text[:3500]
        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("resume_agent", self.prompt_version),
            developer_prompt=get_developer_prompt("resume_agent", self.prompt_version),
            user_content=f"Resume Raw Text:\n{clean_text}",
        )

        analysis: ResumeAnalysis = self._invoke_structured(messages, ResumeAnalysis, retry_feedback)

        return {"resume_data": analysis.model_dump()}

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        return {
            "resume_data": ResumeAnalysis().model_dump(),
            "is_failed": True,
            "error_log": [{"agent": self.agent_name, "error": error}],
        }
