"""
Pydantic schemas for request/response bodies.
"""

from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    AuthResponse,
)
from app.schemas.resume import ResumeResponse
from app.schemas.job_description import (
    JobDescriptionCreateRequest,
    JobDescriptionResponse,
    JobDescriptionMatchResponse,
)
from app.schemas.interview import (
    InterviewCreateRequest,
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewStatusResponse,
    InterviewPlanResponse,
    BlueprintApprovalRequest,
    BlueprintApprovalResponse,
)
from app.schemas.report import (
    InterviewReportResponse,
    ReportHistoryItem,
    CompetencyScoreItem,
    ImprovementPlanItem,
    TranscriptSnapshotItem,
)
from app.schemas.user import UserUpdateRequest
from app.schemas.agent_contracts import (
    AgentError,
    AgentErrorCode,
    AgentResult,
    ResumeAgentInput,
    ResumeAnalysis,
    JDAnalysisInput,
    JDAnalysis,
    InterviewPlanInput,
    InterviewPlan,
    QuestionGenerationInput,
    GeneratedQuestion,
    AnswerEvaluationInput,
    AnswerEvaluation,
    ReportGenerationInput,
    InterviewReport,
    InterviewContext,
)

__all__ = [
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "AuthResponse",
    "ResumeResponse",
    "JobDescriptionCreateRequest",
    "JobDescriptionResponse",
    "InterviewCreateRequest",
    "InterviewAnswerRequest",
    "InterviewAnswerResponse",
    "InterviewStatusResponse",
    "InterviewPlanResponse",
    "BlueprintApprovalRequest",
    "BlueprintApprovalResponse",
    "InterviewReportResponse",
    "ReportHistoryItem",
    "CompetencyScoreItem",
    "ImprovementPlanItem",
    "TranscriptSnapshotItem",
    "UserUpdateRequest",
    "AgentError",
    "AgentErrorCode",
    "AgentResult",
    "ResumeAgentInput",
    "ResumeAnalysis",
    "JDAnalysisInput",
    "JDAnalysis",
    "InterviewPlanInput",
    "InterviewPlan",
    "QuestionGenerationInput",
    "GeneratedQuestion",
    "AnswerEvaluationInput",
    "AnswerEvaluation",
    "ReportGenerationInput",
    "InterviewReport",
    "InterviewContext",
]
