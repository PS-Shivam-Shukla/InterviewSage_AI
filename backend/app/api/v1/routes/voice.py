"""
Voice & Live Session API Router.
Exposes endpoints for voice metrics analytics and live interview session monitoring.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.speech.analytics import VoiceAnalyticsService
from app.transcript.schemas import VoiceMetricsResponse

router = APIRouter(prefix="/voice", tags=["Voice Analytics"])


@router.get("/{session_id}", response_model=VoiceMetricsResponse, summary="Retrieve voice metrics for a live session")
async def get_voice_metrics_by_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analytics = VoiceAnalyticsService(db)
    metrics = analytics.compute_session_voice_metrics(session_id)
    return VoiceMetricsResponse(
        id=metrics.id,
        session_id=metrics.session_id,
        candidate_id=metrics.candidate_id,
        avg_speaking_speed_wpm=metrics.avg_speaking_speed_wpm,
        total_speaking_time_seconds=metrics.total_speaking_time_seconds,
        total_silence_duration_seconds=metrics.total_silence_duration_seconds,
        answer_latency_avg_seconds=metrics.answer_latency_avg_seconds,
        total_words_spoken=metrics.total_words_spoken,
        technical_score=metrics.technical_score,
        communication_score=metrics.communication_score,
        confidence_estimate=metrics.confidence_estimate,
        updated_at=metrics.updated_at.isoformat(),
    )
