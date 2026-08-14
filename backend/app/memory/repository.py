"""
Memory Repository — Database access layer for candidate profiles, memories, skill progression, recommendations, and summaries.
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.candidate_memory import (
    CandidateMemory,
    CandidateProfile,
    LearningRecommendation,
    MemorySummary,
    SkillProgress,
)


class MemoryRepository:
    """Repository handling SQL operations for Candidate Memory & Personalization."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Candidate Profile ─────────────────────────────────────

    def get_profile(self, candidate_id: str) -> CandidateProfile | None:
        return (
            self.db.query(CandidateProfile)
            .filter(CandidateProfile.candidate_id == candidate_id)
            .first()
        )

    def get_or_create_profile(self, candidate_id: str) -> CandidateProfile:
        profile = self.get_profile(candidate_id)
        if not profile:
            profile = CandidateProfile(
                candidate_id=candidate_id,
                experience_years=0,
                skills="[]",
                current_level="MID",
                strengths="[]",
                weaknesses="[]",
                summary="Initial candidate profile.",
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def update_profile(
        self,
        candidate_id: str,
        experience_years: int | None = None,
        skills: list[str] | None = None,
        level: str | None = None,
        strengths: list[str] | None = None,
        weaknesses: list[str] | None = None,
        summary: str | None = None,
    ) -> CandidateProfile:
        profile = self.get_or_create_profile(candidate_id)
        if experience_years is not None:
            profile.experience_years = experience_years
        if skills is not None:
            profile.set_skills(skills)
        if level is not None:
            profile.current_level = level
        if strengths is not None:
            profile.set_strengths(strengths)
        if weaknesses is not None:
            profile.set_weaknesses(weaknesses)
        if summary is not None:
            profile.summary = summary
        self.db.commit()
        self.db.refresh(profile)
        return profile

    # ── Candidate Memories ───────────────────────────────────

    def create_memory(
        self,
        candidate_id: str,
        summary: str,
        interview_id: str | None = None,
        memory_type: str = "EPISODIC",
        key_topics: list[str] | None = None,
        embedding: list[float] | None = None,
    ) -> CandidateMemory:
        mem = CandidateMemory(
            candidate_id=candidate_id,
            interview_id=interview_id,
            memory_type=memory_type,
            summary=summary,
            key_topics=json.dumps(key_topics or []),
            embedding=json.dumps(embedding) if embedding else None,
        )
        self.db.add(mem)
        self.db.commit()
        self.db.refresh(mem)
        return mem

    def list_memories(
        self, candidate_id: str, memory_type: str | None = None, limit: int = 20
    ) -> list[CandidateMemory]:
        q = self.db.query(CandidateMemory).filter(CandidateMemory.candidate_id == candidate_id)
        if memory_type:
            q = q.filter(CandidateMemory.memory_type == memory_type)
        return q.order_by(CandidateMemory.created_at.desc()).limit(limit).all()

    # ── Skill Progress ───────────────────────────────────────

    def get_skill_progress(self, candidate_id: str, skill_name: str) -> SkillProgress | None:
        return (
            self.db.query(SkillProgress)
            .filter(
                SkillProgress.candidate_id == candidate_id, SkillProgress.skill_name == skill_name
            )
            .first()
        )

    def list_skill_progress(self, candidate_id: str) -> list[SkillProgress]:
        return (
            self.db.query(SkillProgress)
            .filter(SkillProgress.candidate_id == candidate_id)
            .order_by(SkillProgress.skill_name.asc())
            .all()
        )

    def upsert_skill_progress(
        self, candidate_id: str, skill_name: str, score: float
    ) -> SkillProgress:
        prog = self.get_skill_progress(candidate_id, skill_name)
        if not prog:
            prog = SkillProgress(
                candidate_id=candidate_id,
                skill_name=skill_name,
                current_score=score,
                best_score=score,
                average_score=score,
                trend="STABLE",
                total_evaluations=1,
            )
            self.db.add(prog)
        else:
            prev_score = prog.current_score
            n = prog.total_evaluations + 1
            new_avg = round(((prog.average_score * prog.total_evaluations) + score) / n, 2)

            # Trend calculation
            if score > prev_score + 2.0:
                trend = "IMPROVING"
            elif score < prev_score - 2.0:
                trend = "REGRESSING"
            else:
                trend = "STABLE"

            prog.current_score = score
            prog.best_score = max(prog.best_score, score)
            prog.average_score = new_avg
            prog.trend = trend
            prog.total_evaluations = n

        self.db.commit()
        self.db.refresh(prog)
        return prog

    # ── Recommendations ─────────────────────────────────────

    def create_recommendation(
        self,
        candidate_id: str,
        target_topic: str,
        suggested_action: str,
        interview_id: str | None = None,
        priority: str = "MEDIUM",
        week_number: int = 1,
    ) -> LearningRecommendation:
        rec = LearningRecommendation(
            candidate_id=candidate_id,
            interview_id=interview_id,
            target_topic=target_topic,
            priority=priority,
            suggested_action=suggested_action,
            week_number=week_number,
        )
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)
        return rec

    def list_recommendations(self, candidate_id: str) -> list[LearningRecommendation]:
        return (
            self.db.query(LearningRecommendation)
            .filter(LearningRecommendation.candidate_id == candidate_id)
            .order_by(
                LearningRecommendation.week_number.asc(), LearningRecommendation.priority.asc()
            )
            .all()
        )

    # ── Memory Summary ────────────────────────────────────────

    def create_summary(
        self,
        candidate_id: str,
        compressed_summary: str,
        interview_count_covered: int,
        key_strengths: list[str] | None = None,
        key_weaknesses: list[str] | None = None,
    ) -> MemorySummary:
        summ = MemorySummary(
            candidate_id=candidate_id,
            compressed_summary=compressed_summary,
            interview_count_covered=interview_count_covered,
            key_strengths=json.dumps(key_strengths or []),
            key_weaknesses=json.dumps(key_weaknesses or []),
        )
        self.db.add(summ)
        self.db.commit()
        self.db.refresh(summ)
        return summ

    def get_latest_summary(self, candidate_id: str) -> MemorySummary | None:
        return (
            self.db.query(MemorySummary)
            .filter(MemorySummary.candidate_id == candidate_id)
            .order_by(MemorySummary.created_at.desc())
            .first()
        )
