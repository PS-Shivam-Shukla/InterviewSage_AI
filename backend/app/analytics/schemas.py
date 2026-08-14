"""
Analytics & Admin Operations Pydantic Schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AdminDashboardSummaryResponse(BaseModel):
    total_interviews: int = 0
    active_interviews: int = 0
    completed_interviews: int = 0
    failed_interviews: int = 0
    success_rate: float = 0.0
    avg_interview_duration_minutes: float = 0.0
    avg_ai_score: float = 0.0
    avg_candidate_score: float = 0.0
    total_ai_requests: int = 0
    avg_latency_ms: float = 0.0
    avg_token_usage: float = 0.0
    total_token_cost_usd: float = 0.0
    hallucination_rate: float = 0.0


class LiveInterviewItem(BaseModel):
    interview_id: str
    candidate_name: str
    current_round: str
    question_number: int
    workflow_stage: str
    current_agent: str
    elapsed_seconds: int
    thread_id: str
    worker_id: str = "worker-01"


class TimelineStep(BaseModel):
    step_number: int
    event_type: str  # QUESTION | ANSWER | EVALUATION | AGENT_LOG | CHECKPOINT
    timestamp: str | None = None
    question_text: str | None = None
    candidate_answer: str | None = None
    score: float | None = None
    reasoning: str | None = None
    next_agent: str | None = None
    checkpoint_id: str | None = None


class InterviewTimelineResponse(BaseModel):
    interview_id: str
    candidate_name: str
    job_title: str
    current_stage: str
    timeline: list[TimelineStep] = Field(default_factory=list)


class PromptHistoryItem(BaseModel):
    prompt_key: str
    version: str
    created_at: str | None = None
    description: str = ""
    is_active: bool = True
    variables: list[str] = Field(default_factory=list)


class RecruiterFeedbackRequest(BaseModel):
    interview_id: str
    question_id: str | None = None
    rating_action: str  # APPROVE | REJECT | NEEDS_REVIEW
    comment: str | None = None


class ReviewQueueItemResponse(BaseModel):
    review_id: str
    interview_id: str
    response_id: str | None = None
    confidence: float
    reason: str
    assigned_admin: str | None = None
    status: str
    created_at: str
