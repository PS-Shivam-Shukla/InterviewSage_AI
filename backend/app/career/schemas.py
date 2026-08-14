"""
Pydantic Schemas for AI Career Intelligence Subsystem.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HiringPredictionResponse(BaseModel):
    candidate_id: str
    hire_probability: float = Field(..., description="Hire probability 0.0 - 100.0%")
    confidence_score: float = Field(..., description="AI confidence score 0.0 - 100.0%")
    outcome: str = Field(..., description="Hire | Borderline | Reject")
    key_reasons: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    drawbacks: list[str] = Field(default_factory=list)


class BenchmarkCategoryDetail(BaseModel):
    category: str
    candidate_score: float
    industry_average: float
    top_10_percentile: float
    percentile: float


class IndustryBenchmarkResponse(BaseModel):
    candidate_id: str
    overall_percentile: float
    categories: list[BenchmarkCategoryDetail]


class CompanyProfileResponse(BaseModel):
    company_name: str
    description: str
    coding_weight: float
    system_design_weight: float
    behavioral_weight: float
    key_principles: list[str]


class AdaptiveStartRequest(BaseModel):
    interview_id: str
    candidate_id: str
    initial_difficulty: float = 5.0


class AdaptiveStartResponse(BaseModel):
    session_id: str
    interview_id: str
    candidate_id: str
    current_difficulty: float
    status: str


class AdaptiveNextQuestionRequest(BaseModel):
    session_id: str
    performance_score: float = Field(..., description="Performance score 0.0 - 100.0")
    response_latency_seconds: float = 0.0


class AdaptiveNextQuestionResponse(BaseModel):
    session_id: str
    previous_difficulty: float
    new_difficulty: float
    adjustment_reason: str
    suggested_focus: str


class SkillGapItem(BaseModel):
    topic: str
    severity: str
    missing_concepts: list[str]


class SkillGapResponse(BaseModel):
    candidate_id: str
    total_gaps: int
    gaps: list[SkillGapItem]


class CareerRoadmapResponse(BaseModel):
    candidate_id: str
    daily_plan: list[dict[str, Any]]
    weekly_plan: list[dict[str, Any]]
    monthly_plan: list[dict[str, Any]]


class InterviewAnnotationItem(BaseModel):
    timestamp_mark: str
    annotation_type: str
    note: str


class InterviewReplayResponse(BaseModel):
    interview_id: str
    total_annotations: int
    annotations: list[InterviewAnnotationItem]


class RecruiterInsightsResponse(BaseModel):
    interview_id: str
    recommendation: str
    ai_confidence: float
    primary_rejection_factors: list[str]
    highest_impact_round: str
    recommended_improvements: list[str]
