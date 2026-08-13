"""
Enterprise AI Platform Admin Operations Router.
Exposes endpoints for AI Admin Dashboard, Live Monitoring, Conversation Replay, Prompt History,
Costs, Quality, Human Review Queue, Recruiter Feedback, and Analytics.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.admin.dashboard import AdminDashboardManager
from app.analytics.schemas import (
    AdminDashboardSummaryResponse,
    InterviewTimelineResponse,
    LiveInterviewItem,
    PromptHistoryItem,
    RecruiterFeedbackRequest,
    ReviewQueueItemResponse,
)
from app.analytics.service import AnalyticsService
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.review.service import ReviewService

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

_ADMIN_EMAILS = {"admin@example.com", "recruiter@example.com"}


def _verify_admin_access(current_user: User = Depends(get_current_user)) -> User:
    if current_user.email not in _ADMIN_EMAILS and not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for AI Platform Operations",
        )
    return current_user


# ── OP-1: AI Admin Dashboard Overview ──────────────────────────────
@router.get("/dashboard", response_model=AdminDashboardSummaryResponse, summary="AI Admin Dashboard Overview")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    mgr = AdminDashboardManager(db)
    return mgr.get_dashboard_overview()


# ── OP-2: Live Interview Monitoring ──────────────────────────────
@router.get("/interviews/live", response_model=List[LiveInterviewItem], summary="Live Interview Monitoring")
async def get_live_interviews(
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    mgr = AdminDashboardManager(db)
    return mgr.get_live_interviews()


# ── OP-3: Conversation Replay Timeline ──────────────────────────────
@router.get("/interview/{interview_id}/timeline", response_model=InterviewTimelineResponse, summary="Conversation Replay Timeline")
async def get_interview_timeline(
    interview_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    mgr = AdminDashboardManager(db)
    return mgr.reconstruct_timeline(interview_id)


# ── OP-4: Prompt History Explorer ──────────────────────────────
@router.get("/prompts/history", response_model=List[PromptHistoryItem], summary="Prompt Version History Explorer")
async def get_prompt_history(
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    mgr = AdminDashboardManager(db)
    return mgr.get_prompt_history_explorer()


# ── OP-5, OP-6, OP-9, OP-10: Analytics APIs ──────────────────────────────
@router.get("/analytics/overview", summary="Analytics Overview")
async def get_analytics_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    service = AnalyticsService(db)
    return service.get_admin_overview()


@router.get("/analytics/models", summary="Model Comparison Analytics")
async def get_model_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    service = AnalyticsService(db)
    return service.get_model_analytics()


@router.get("/analytics/costs", summary="AI Cost Dashboard Breakdown")
async def get_cost_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    service = AnalyticsService(db)
    return service.get_cost_analytics()


@router.get("/analytics/evaluations", summary="AI Quality & Evaluation Analytics")
async def get_evaluation_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    service = AnalyticsService(db)
    return service.repo.get_evaluation_quality_metrics()


@router.get("/analytics/interviews", summary="Interview Metrics Analytics")
async def get_interview_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    service = AnalyticsService(db)
    return service.repo.get_interview_counts()


@router.get("/analytics/agents", summary="Agent Metrics Analytics")
async def get_agent_analytics(
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    service = AnalyticsService(db)
    return service.get_agent_metrics()


# ── OP-7: Human Review Queue ──────────────────────────────
@router.get("/review/queue", response_model=List[ReviewQueueItemResponse], summary="Get Human Review Queue")
async def get_review_queue(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    service = ReviewService(db)
    items = service.get_queue(status=status_filter)
    return [
        ReviewQueueItemResponse(
            review_id=item.id,
            interview_id=item.interview_id,
            response_id=item.response_id,
            confidence=item.confidence,
            reason=item.reason,
            assigned_admin=item.assigned_admin,
            status=item.status,
            created_at=item.created_at.isoformat(),
        )
        for item in items
    ]


@router.post("/review/{review_id}/status", summary="Process Review Queue Item Status")
async def process_review_status(
    review_id: str,
    status_val: str = Query(..., alias="status"),
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    service = ReviewService(db)
    res = service.process_review(review_id=review_id, status=status_val, admin_id=admin.id)
    if not res:
        raise HTTPException(status_code=404, detail="Review item not found")
    return {"message": "Review item updated successfully", "status": res.status}


# ── OP-8: Recruiter Feedback API ──────────────────────────────
@router.post("/feedback", summary="Submit Recruiter Qualitative Feedback")
async def submit_recruiter_feedback(
    payload: RecruiterFeedbackRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(_verify_admin_access),
):
    service = ReviewService(db)
    fb = service.record_feedback(
        interview_id=payload.interview_id,
        recruiter_id=admin.id,
        rating_action=payload.rating_action,
        question_id=payload.question_id,
        comment=payload.comment,
    )
    return {"message": "Recruiter feedback recorded", "feedback_id": fb.id}


# Legacy compatibility endpoint
@router.get("/agent-metrics", summary="Agent health, latency, and retry metrics")
async def agent_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.email not in _ADMIN_EMAILS and not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    service = AnalyticsService(db)
    return {"metrics": service.get_agent_metrics()}
