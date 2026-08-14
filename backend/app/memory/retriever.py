"""
Memory Retriever — Serves contextual candidate memory before and during interviews.
Constructs memory retrieval payloads for LangGraph agents & LLM prompt builders.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.memory.repository import MemoryRepository
from app.memory.schemas import (
    CandidateMemoryResponse,
    MemoryRetrievalContext,
    SkillProgressResponse,
)


class MemoryRetriever:
    """Retrieves and formats candidate memory context for agents and workflows."""

    def __init__(self, db: Session) -> None:
        self.repo = MemoryRepository(db)

    def retrieve_context(self, candidate_id: str) -> MemoryRetrievalContext:
        """
        Build complete MemoryRetrievalContext for a candidate.
        Includes profile, past memories, skill progression, and latest compressed summary.
        """
        profile = self.repo.get_or_create_profile(candidate_id)
        memories = self.repo.list_memories(candidate_id, limit=10)
        skills = self.repo.list_skill_progress(candidate_id)
        latest_summ = self.repo.get_latest_summary(candidate_id)

        mem_responses = [
            CandidateMemoryResponse(
                id=m.id,
                candidate_id=m.candidate_id,
                interview_id=m.interview_id,
                memory_type=m.memory_type,
                summary=m.summary,
                key_topics=m.get_topics(),
                created_at=m.created_at.isoformat(),
            )
            for m in memories
        ]

        skill_responses = [
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

        return MemoryRetrievalContext(
            candidate_id=candidate_id,
            total_past_interviews=len(memories),
            profile_level=profile.current_level,
            strengths=profile.get_strengths(),
            weaknesses=profile.get_weaknesses(),
            top_memories=mem_responses,
            skill_progression=skill_responses,
            latest_summary=latest_summ.compressed_summary if latest_summ else profile.summary,
        )

    def search_semantic_memory(
        self, candidate_id: str, query_topic: str
    ) -> list[CandidateMemoryResponse]:
        """
        Search candidate memories for a given query topic.
        """
        memories = self.repo.list_memories(candidate_id, limit=50)
        matched = []
        query_lower = query_topic.lower()

        for m in memories:
            topics = [t.lower() for t in m.get_topics()]
            if query_lower in m.summary.lower() or any(query_lower in t for t in topics):
                matched.append(
                    CandidateMemoryResponse(
                        id=m.id,
                        candidate_id=m.candidate_id,
                        interview_id=m.interview_id,
                        memory_type=m.memory_type,
                        summary=m.summary,
                        key_topics=m.get_topics(),
                        created_at=m.created_at.isoformat(),
                    )
                )

        return matched

    def format_agent_prompt_context(self, candidate_id: str) -> str:
        """
        Format memory retrieval into a human-readable prompt string for LLM agents.
        """
        ctx = self.retrieve_context(candidate_id)
        if (
            ctx.total_past_interviews == 0
            and not ctx.skill_progression
            and not ctx.strengths
            and not ctx.weaknesses
        ):
            return "No previous interview memory recorded for candidate."

        lines = [
            f"=== Candidate Memory Profile ({ctx.profile_level}) ===",
            f"Previous Interviews Evaluated: {ctx.total_past_interviews}",
            f"Known Strengths: {', '.join(ctx.strengths) if ctx.strengths else 'None recorded'}",
            f"Known Weaknesses / Target Focus: {', '.join(ctx.weaknesses) if ctx.weaknesses else 'None recorded'}",
        ]

        if ctx.skill_progression:
            lines.append("Skill Trends:")
            for s in ctx.skill_progression:
                lines.append(f"  - {s.skill_name}: Score {s.current_score} ({s.trend})")

        if ctx.latest_summary:
            lines.append(f"Memory Summary: {ctx.latest_summary}")

        return "\n".join(lines)
