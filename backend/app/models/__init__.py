"""
SQLAlchemy ORM models.
Import all models here so Alembic's autogenerate detects them.
"""

from app.models.base import Base
from app.models.user import User
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.interview import (
    Interview,
    CompetencyMatrix,
    InterviewPlan,
    InterviewQuestion,
    InterviewAnswer,
    Evaluation,
    InterviewReport,
    AgentLog,
)
from app.models.llm_audit import (
    PromptVersion,
    LLMRequest,
    LLMResponse,
    TokenUsage,
)
from app.models.evaluation import (
    EvaluationRun,
    EvaluationResult,
    BenchmarkResult,
    PromptScore,
    ModelScore,
)
from app.models.review_queue import (
    ReviewQueue,
    RecruiterFeedback,
)
from app.models.candidate_memory import (
    CandidateProfile,
    CandidateMemory,
    SkillProgress,
    LearningRecommendation,
    MemorySummary,
)
from app.models.voice import (
    LiveSession,
    ConversationTurn,
    VoiceMetrics,
    SpeechEvent,
    TranscriptExport,
)
from app.models.career import (
    AdaptiveSession,
    DifficultyHistory,
    CompanyProfile,
    IndustryBenchmark,
    CandidatePrediction,
    SkillGapAnalysis,
    CareerRoadmap,
    InterviewAnnotation,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
)

__all__ = [
    "Base",
    "User",
    "Resume",
    "JobDescription",
    "Interview",
    "CompetencyMatrix",
    "InterviewPlan",
    "InterviewQuestion",
    "InterviewAnswer",
    "Evaluation",
    "InterviewReport",
    "AgentLog",
    "PromptVersion",
    "LLMRequest",
    "LLMResponse",
    "TokenUsage",
    "EvaluationRun",
    "EvaluationResult",
    "BenchmarkResult",
    "PromptScore",
    "ModelScore",
    "ReviewQueue",
    "RecruiterFeedback",
    "CandidateProfile",
    "CandidateMemory",
    "SkillProgress",
    "LearningRecommendation",
    "MemorySummary",
    "LiveSession",
    "ConversationTurn",
    "VoiceMetrics",
    "SpeechEvent",
    "TranscriptExport",
    "AdaptiveSession",
    "DifficultyHistory",
    "CompanyProfile",
    "IndustryBenchmark",
    "CandidatePrediction",
    "SkillGapAnalysis",
    "CareerRoadmap",
    "InterviewAnnotation",
    "KnowledgeGraphNode",
    "KnowledgeGraphEdge",
]
