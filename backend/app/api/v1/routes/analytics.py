"""
Analytics routes — cross-interview aggregation endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", summary="Dashboard summary stats")
async def analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalyticsService(db)
    data = service.get_summary(current_user.id)
    # Keep backward-compatible envelope expected by existing tests
    return {"summary": data}


@router.get("/trends", summary="Score trend over time")
async def analytics_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalyticsService(db)
    return {"trends": service.get_trends(current_user.id)}


@router.get("/competencies", summary="Aggregate competency radar data")
async def analytics_competencies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalyticsService(db)
    return {"competencies": service.get_competencies(current_user.id)}


@router.get("/voice", summary="Aggregate candidate voice performance metrics")
async def analytics_voice(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalyticsService(db)
    return {"voice": service.get_voice_summary(current_user.id)}
