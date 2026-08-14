from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompetencyScoreItem(BaseModel):
    competency: str
    score: float
    fullMark: int = 100


class ImprovementPlanItem(BaseModel):
    id: str
    topic: str
    description: str
    targetSkill: str
    priority: str


class TranscriptSnapshotItem(BaseModel):
    question: str
    answer: str
    score: float
    reasoning: str


class InterviewReportResponse(BaseModel):
    interview_id: str
    status: str = "COMPLETED"
    overall_score: float = 85.0
    role: str = "Python Backend Engineer"
    competency_scorecard: list[CompetencyScoreItem]
    improvement_plan: list[ImprovementPlanItem]
    transcript_snapshot: list[TranscriptSnapshotItem]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportHistoryItem(BaseModel):
    interview_id: str
    role: str
    status: str
    overall_score: float
    generated_at: datetime
    completed_at: datetime | None = None
    total_questions: int = 0

    model_config = ConfigDict(from_attributes=True)
