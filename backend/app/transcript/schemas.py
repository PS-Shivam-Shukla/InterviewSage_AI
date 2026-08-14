"""
Pydantic Schemas for Transcript & Voice Interview Engine.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConversationTurnCreate(BaseModel):
    speaker: str = Field("CANDIDATE", description="CANDIDATE | AI_AGENT | SYSTEM")
    transcript: str = Field(..., description="Transcript text of the spoken turn")
    duration_seconds: float = Field(0.0, description="Duration in seconds")
    tokens_used: int = Field(0, description="Tokens consumed")
    agent_name: str = Field("TechnicalInterviewAgent", description="Interviewer agent name")


class ConversationTurnResponse(BaseModel):
    id: str
    session_id: str
    turn_number: int
    speaker: str
    transcript: str
    duration_seconds: float
    tokens_used: int
    agent_name: str
    created_at: str

    class Config:
        from_attributes = True


class VoiceMetricsResponse(BaseModel):
    id: str
    session_id: str
    candidate_id: str
    avg_speaking_speed_wpm: float
    total_speaking_time_seconds: float
    total_silence_duration_seconds: float
    answer_latency_avg_seconds: float
    total_words_spoken: int
    technical_score: float | None = None
    communication_score: float
    confidence_estimate: float
    updated_at: str

    class Config:
        from_attributes = True


class LiveSessionResponse(BaseModel):
    id: str
    interview_id: str
    candidate_id: str
    status: str
    active_worker_id: str
    started_at: str
    ended_at: str | None = None
    turns_count: int = 0

    class Config:
        from_attributes = True


class TranscriptExportResponse(BaseModel):
    id: str
    interview_id: str
    session_id: str
    full_text: str
    turn_count: int
    file_path: str | None = None
    created_at: str

    class Config:
        from_attributes = True


class LiveScoreUpdate(BaseModel):
    session_id: str
    turn_number: int
    technical_score: float
    communication_score: float
    confidence_estimate: float
    overall_progress: float
    current_agent: str
