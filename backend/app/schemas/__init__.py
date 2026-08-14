"""
Pydantic schemas for request/response bodies.
"""

from app.schemas.agent_contracts import (
    AgentError,
    AgentErrorCode,
    AgentResult,
    AnswerEvaluation,
    AnswerEvaluationInput,
    GeneratedQuestion,
    InterviewContext,
    InterviewPlan,
    InterviewPlanInput,
    InterviewReport,
    JDAnalysis,
    JDAnalysisInput,
    QuestionGenerationInput,
    ReportGenerationInput,
    ResumeAgentInput,
    ResumeAnalysis,
)
from app.schemas.auth import (
    AuthResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.interview import (
    BlueprintApprovalRequest,
    BlueprintApprovalResponse,
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewCreateRequest,
    InterviewPlanResponse,
    InterviewStatusResponse,
)
from app.schemas.job_description import (
    JobDescriptionCreateRequest,
    JobDescriptionMatchResponse,
    JobDescriptionResponse,
)
from app.schemas.report import (
    CompetencyScoreItem,
    ImprovementPlanItem,
    InterviewReportResponse,
    ReportHistoryItem,
    TranscriptSnapshotItem,
)
from app.schemas.resume import ResumeResponse
from app.schemas.user import UserUpdateRequest

__all__ = [
    "AgentError",
    "AgentErrorCode",
    "AgentResult",
    "AnswerEvaluation",
    "AnswerEvaluationInput",
    "AuthResponse",
    "BlueprintApprovalRequest",
    "BlueprintApprovalResponse",
    "CompetencyScoreItem",
    "GeneratedQuestion",
    "ImprovementPlanItem",
    "InterviewAnswerRequest",
    "InterviewAnswerResponse",
    "InterviewContext",
    "InterviewCreateRequest",
    "InterviewPlan",
    "InterviewPlanInput",
    "InterviewPlanResponse",
    "InterviewReport",
    "InterviewReportResponse",
    "InterviewStatusResponse",
    "JDAnalysis",
    "JDAnalysisInput",
    "JobDescriptionCreateRequest",
    "JobDescriptionMatchResponse",
    "JobDescriptionResponse",
    "QuestionGenerationInput",
    "ReportGenerationInput",
    "ReportHistoryItem",
    "ResumeAgentInput",
    "ResumeAnalysis",
    "ResumeResponse",
    "TokenResponse",
    "TranscriptSnapshotItem",
    "UserLoginRequest",
    "UserRegisterRequest",
    "UserResponse",
    "UserUpdateRequest",
]
