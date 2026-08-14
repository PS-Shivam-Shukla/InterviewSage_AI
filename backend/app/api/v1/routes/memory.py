"""
Candidate Memory & Personalization API Router.
Exposes endpoints for retrieving candidate memory profiles, saving new interview memories,
querying interview history timelines, inspecting skill progressions, fetching learning roadmaps,
and triggering memory compression summaries.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user
from app.memory.schemas import (
    CandidateMemoryCreate,
    CandidateMemoryResponse,
    CandidateProfileResponse,
    CandidateTimelineItem,
    LearningRecommendationResponse,
    MemorySummaryResponse,
    SkillProgressResponse,
)
from app.memory.service import MemoryService
from app.models import User

router = APIRouter(prefix="/memory", tags=["Candidate Memory"])

_ADMIN_EMAILS = {"admin@example.com", "recruiter@example.com"}


def _verify_candidate_ownership_or_admin(candidate_id: str, current_user: User) -> None:
    is_owner = current_user.id == candidate_id
    is_admin = current_user.email in _ADMIN_EMAILS or getattr(current_user, "is_admin", False)
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot access another candidate's memory profile",
        )


@router.get("/{candidate_id}", response_model=CandidateProfileResponse, summary="Retrieve candidate memory profile")
async def get_candidate_memory(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_candidate_ownership_or_admin(candidate_id, current_user)
    service = MemoryService(db)
    return service.get_candidate_memory(candidate_id)


@router.post("/{candidate_id}", response_model=CandidateMemoryResponse, summary="Save a new candidate memory")
async def save_candidate_memory(
    candidate_id: str,
    payload: CandidateMemoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_candidate_ownership_or_admin(candidate_id, current_user)
    service = MemoryService(db)
    return service.save_memory(candidate_id, payload)


@router.get("/{candidate_id}/timeline", response_model=list[CandidateTimelineItem], summary="Get interview memory timeline")
async def get_candidate_timeline(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_candidate_ownership_or_admin(candidate_id, current_user)
    service = MemoryService(db)
    return service.get_timeline(candidate_id)


@router.get("/{candidate_id}/skills", response_model=list[SkillProgressResponse], summary="Get skill progression graph")
async def get_skill_progression(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_candidate_ownership_or_admin(candidate_id, current_user)
    service = MemoryService(db)
    return service.get_skills(candidate_id)


@router.get("/{candidate_id}/recommendations", response_model=list[LearningRecommendationResponse], summary="Get personalized learning roadmap")
async def get_learning_recommendations(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_candidate_ownership_or_admin(candidate_id, current_user)
    service = MemoryService(db)
    return service.get_recommendations(candidate_id)


@router.post("/{candidate_id}/summarize", response_model=MemorySummaryResponse, summary="Compress interview memories into summary")
async def compress_candidate_memories(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_candidate_ownership_or_admin(candidate_id, current_user)
    service = MemoryService(db)
    return service.compress_memories(candidate_id)
