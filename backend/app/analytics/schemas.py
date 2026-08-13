"""
Analytics & Admin Operations Pydantic Schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
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
    timestamp: Optional[str] = None
    question_text: Optional[str] = None
    candidate_answer: Optional[str] = None
    score: Optional[float] = None
    reasoning: Optional[str] = None
    next_agent: Optional[str] = None
    checkpoint_id: Optional[str] = None


class InterviewTimelineResponse(BaseModel):
    interview_id: str
    candidate_name: str
    job_title: str
    current_stage: str
    timeline: List[TimelineStep] = Field(default_factory=list)


class PromptHistoryItem(BaseModel):
    prompt_key: str
    version: str
    created_at: Optional[str] = None
    description: str = ""
    is_active: bool = True
    variables: List[str] = Field(default_factory=list)


class RecruiterFeedbackRequest(BaseModel):
    interview_id: str
    question_id: Optional[str] = None
    rating_action: str  # APPROVE | REJECT | NEEDS_REVIEW
    comment: Optional[str] = None


class ReviewQueueItemResponse(BaseModel):
    review_id: str
    interview_id: str
    response_id: Optional[str] = None
    confidence: float
    reason: str
    assigned_admin: Optional[str] = None
    status: str
    created_at: str
