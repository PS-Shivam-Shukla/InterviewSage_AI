"""
Analytics Package Exports.
"""

from app.analytics.repository import AnalyticsRepository
from app.analytics.schemas import (
    AdminDashboardSummaryResponse,
    InterviewTimelineResponse,
    LiveInterviewItem,
    PromptHistoryItem,
    RecruiterFeedbackRequest,
    ReviewQueueItemResponse,
    TimelineStep,
)

def __getattr__(name: str):
    if name == "AnalyticsService":
        from app.services.analytics_service import AnalyticsService
        return AnalyticsService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "AnalyticsRepository",
    "AnalyticsService",
    "AdminDashboardSummaryResponse",
    "LiveInterviewItem",
    "TimelineStep",
    "InterviewTimelineResponse",
    "PromptHistoryItem",
    "RecruiterFeedbackRequest",
    "ReviewQueueItemResponse",
]
