"""
Pydantic Schemas for Candidate Memory & Personalization Engine.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateProfileBase(BaseModel):
    experience_years: int = Field(0, description="Candidate years of experience")
    skills: list[str] = Field(default_factory=list, description="Verified candidate skills")
    current_level: str = Field("MID", description="Current engineering level")
    strengths: list[str] = Field(default_factory=list, description="Identified strength topics")
    weaknesses: list[str] = Field(default_factory=list, description="Identified weakness topics")
    summary: str | None = Field(None, description="Longitudinal profile summary")


class CandidateProfileResponse(CandidateProfileBase):
    id: str
    candidate_id: str
    updated_at: str

    class Config:
        from_attributes = True


class CandidateMemoryCreate(BaseModel):
    interview_id: str | None = None
    memory_type: str = Field("EPISODIC", description="EPISODIC | SEMANTIC | SUMMARY")
    summary: str = Field(..., description="Memory text summary")
    key_topics: list[str] = Field(default_factory=list, description="Associated key topics")
    embedding: list[float] | None = Field(
        None, description="Optional vector embedding representation"
    )


class CandidateMemoryResponse(BaseModel):
    id: str
    candidate_id: str
    interview_id: str | None = None
    memory_type: str
    summary: str
    key_topics: list[str]
    created_at: str

    class Config:
        from_attributes = True


class SkillProgressResponse(BaseModel):
    id: str
    candidate_id: str
    skill_name: str
    current_score: float
    best_score: float
    average_score: float
    trend: str  # IMPROVING | REGRESSING | STABLE
    total_evaluations: int
    updated_at: str

    class Config:
        from_attributes = True


class LearningRecommendationResponse(BaseModel):
    id: str
    candidate_id: str
    interview_id: str | None = None
    target_topic: str
    priority: str  # HIGH | MEDIUM | LOW
    suggested_action: str
    week_number: int
    created_at: str

    class Config:
        from_attributes = True


class MemorySummaryResponse(BaseModel):
    id: str
    candidate_id: str
    compressed_summary: str
    interview_count_covered: int
    key_strengths: list[str]
    key_weaknesses: list[str]
    created_at: str

    class Config:
        from_attributes = True


class MemoryRetrievalContext(BaseModel):
    candidate_id: str
    total_past_interviews: int
    profile_level: str
    strengths: list[str]
    weaknesses: list[str]
    top_memories: list[CandidateMemoryResponse]
    skill_progression: list[SkillProgressResponse]
    latest_summary: str | None = None


class PersonalizedQuestionRecommendation(BaseModel):
    target_skill: str
    recommended_difficulty: str
    suggested_focus: str
    reasoning: str


class CandidateTimelineItem(BaseModel):
    interview_id: str
    date: str
    overall_score: float | None = None
    summary: str
    key_topics: list[str]
