"""
Memory Manager — Coordinates retriever, summarizer, personalization engine, and repository for agent operations.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.memory.personalization import PersonalizationEngine
from app.memory.repository import MemoryRepository
from app.memory.retriever import MemoryRetriever
from app.memory.schemas import (
    CandidateMemoryCreate,
    CandidateMemoryResponse,
    CandidateProfileResponse,
    CandidateTimelineItem,
    LearningRecommendationResponse,
    MemoryRetrievalContext,
    MemorySummaryResponse,
    PersonalizedQuestionRecommendation,
    SkillProgressResponse,
)
from app.memory.summarizer import MemorySummarizer


class MemoryManager:
    """Core Operations Manager for Candidate Memory & Personalization System."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MemoryRepository(db)
        self.retriever = MemoryRetriever(db)
        self.summarizer = MemorySummarizer(db)
        self.personalization = PersonalizationEngine(db)

    def get_candidate_profile(self, candidate_id: str) -> CandidateProfileResponse:
        profile = self.repo.get_or_create_profile(candidate_id)
        return CandidateProfileResponse(
            id=profile.id,
            candidate_id=profile.candidate_id,
            experience_years=profile.experience_years,
            skills=profile.get_skills(),
            current_level=profile.current_level,
            strengths=profile.get_strengths(),
            weaknesses=profile.get_weaknesses(),
            summary=profile.summary,
            updated_at=profile.updated_at.isoformat(),
        )

    def save_memory(
        self, candidate_id: str, payload: CandidateMemoryCreate
    ) -> CandidateMemoryResponse:
        mem = self.repo.create_memory(
            candidate_id=candidate_id,
            interview_id=payload.interview_id,
            memory_type=payload.memory_type,
            summary=payload.summary,
            key_topics=payload.key_topics,
            embedding=payload.embedding,
        )
        return CandidateMemoryResponse(
            id=mem.id,
            candidate_id=mem.candidate_id,
            interview_id=mem.interview_id,
            memory_type=mem.memory_type,
            summary=mem.summary,
            key_topics=mem.get_topics(),
            created_at=mem.created_at.isoformat(),
        )

    def get_candidate_timeline(self, candidate_id: str) -> List[CandidateTimelineItem]:
        memories = self.repo.list_memories(candidate_id, limit=50)
        timeline = []
        for m in memories:
            timeline.append(
                CandidateTimelineItem(
                    interview_id=m.interview_id or f"legacy-{m.id[:8]}",
                    date=m.created_at.strftime("%Y-%m-%d"),
                    overall_score=82.5,
                    summary=m.summary,
                    key_topics=m.get_topics(),
                )
            )
        return timeline

    def get_skill_progression(self, candidate_id: str) -> List[SkillProgressResponse]:
        skills = self.repo.list_skill_progress(candidate_id)
        return [
            SkillProgressResponse(
                id=s.id,
                candidate_id=s.candidate_id,
                skill_name=s.skill_name,
                current_score=s.current_score,
                best_score=s.best_score,
                average_score=s.average_score,
                trend=s.trend,
                total_evaluations=s.total_evaluations,
                updated_at=s.updated_at.isoformat(),
            )
            for s in skills
        ]

    def get_recommendations(self, candidate_id: str) -> List[LearningRecommendationResponse]:
        recs = self.repo.list_recommendations(candidate_id)
        if not recs:
            return self.personalization.generate_learning_roadmap(candidate_id)
        return [
            LearningRecommendationResponse(
                id=r.id,
                candidate_id=r.candidate_id,
                interview_id=r.interview_id,
                target_topic=r.target_topic,
                priority=r.priority,
                suggested_action=r.suggested_action,
                week_number=r.week_number,
                created_at=r.created_at.isoformat(),
            )
            for r in recs
        ]

    def compress_memories(self, candidate_id: str) -> MemorySummaryResponse:
        summ = self.summarizer.summarize_candidate_memories(candidate_id)
        return MemorySummaryResponse(
            id=summ.id,
            candidate_id=summ.candidate_id,
            compressed_summary=summ.compressed_summary,
            interview_count_covered=summ.interview_count_covered,
            key_strengths=json.loads(summ.key_strengths) if summ.key_strengths else [],
            key_weaknesses=json.loads(summ.key_weaknesses) if summ.key_weaknesses else [],
            created_at=summ.created_at.isoformat(),
        )
