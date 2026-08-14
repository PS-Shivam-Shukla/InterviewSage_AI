"""
SQLAlchemy ORM models.
Import all models here so Alembic's autogenerate detects them.
"""

from app.models.base import Base
from app.models.candidate_memory import (
    CandidateMemory,
    CandidateProfile,
    LearningRecommendation,
    MemorySummary,
    SkillProgress,
)
from app.models.career import (
    AdaptiveSession,
    CandidatePrediction,
    CareerRoadmap,
    CompanyProfile,
    DifficultyHistory,
    IndustryBenchmark,
    InterviewAnnotation,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    SkillGapAnalysis,
)
from app.models.evaluation import (
    BenchmarkResult,
    EvaluationResult,
    EvaluationRun,
    ModelScore,
    PromptScore,
)
from app.models.interview import (
    AgentLog,
    CompetencyMatrix,
    Evaluation,
    Interview,
    InterviewAnswer,
    InterviewPlan,
    InterviewQuestion,
    InterviewReport,
)
from app.models.job_description import JobDescription
from app.models.llm_audit import (
    LLMRequest,
    LLMResponse,
    PromptVersion,
    TokenUsage,
)
from app.models.resume import Resume
from app.models.review_queue import (
    RecruiterFeedback,
    ReviewQueue,
)
from app.models.user import User
from app.models.voice import (
    ConversationTurn,
    LiveSession,
    SpeechEvent,
    TranscriptExport,
    VoiceMetrics,
)

__all__ = [
    "AdaptiveSession",
    "AgentLog",
    "Base",
    "BenchmarkResult",
    "CandidateMemory",
    "CandidatePrediction",
    "CandidateProfile",
    "CareerRoadmap",
    "CompanyProfile",
    "CompetencyMatrix",
    "ConversationTurn",
    "DifficultyHistory",
    "Evaluation",
    "EvaluationResult",
    "EvaluationRun",
    "IndustryBenchmark",
    "Interview",
    "InterviewAnnotation",
    "InterviewAnswer",
    "InterviewPlan",
    "InterviewQuestion",
    "InterviewReport",
    "JobDescription",
    "KnowledgeGraphEdge",
    "KnowledgeGraphNode",
    "LLMRequest",
    "LLMResponse",
    "LearningRecommendation",
    "LiveSession",
    "MemorySummary",
    "ModelScore",
    "PromptScore",
    "PromptVersion",
    "RecruiterFeedback",
    "Resume",
    "ReviewQueue",
    "SkillGapAnalysis",
    "SkillProgress",
    "SpeechEvent",
    "TokenUsage",
    "TranscriptExport",
    "User",
    "VoiceMetrics",
]
