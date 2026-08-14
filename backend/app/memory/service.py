"""
Memory Service — High-level business service layer for Candidate Memory & Personalization Engine.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.memory.manager import MemoryManager
from app.memory.schemas import (
    CandidateMemoryCreate,
    CandidateMemoryResponse,
    CandidateProfileResponse,
    CandidateTimelineItem,
    LearningRecommendationResponse,
    MemorySummaryResponse,
    SkillProgressResponse,
)


class MemoryService:
    """Service providing candidate memory capabilities to API routes."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.manager = MemoryManager(db)

    def get_candidate_memory(self, candidate_id: str) -> CandidateProfileResponse:
        return self.manager.get_candidate_profile(candidate_id)

    def save_memory(
        self, candidate_id: str, payload: CandidateMemoryCreate
    ) -> CandidateMemoryResponse:
        return self.manager.save_memory(candidate_id, payload)

    def get_timeline(self, candidate_id: str) -> list[CandidateTimelineItem]:
        return self.manager.get_candidate_timeline(candidate_id)

    def get_skills(self, candidate_id: str) -> list[SkillProgressResponse]:
        return self.manager.get_skill_progression(candidate_id)

    def get_recommendations(self, candidate_id: str) -> list[LearningRecommendationResponse]:
        return self.manager.get_recommendations(candidate_id)

    def compress_memories(self, candidate_id: str) -> MemorySummaryResponse:
        return self.manager.compress_memories(candidate_id)
