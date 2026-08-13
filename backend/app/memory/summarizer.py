"""
Memory Summarizer — Compresses multiple interview memories into consolidated summaries.
Reduces token overhead for historical candidate context.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.memory.repository import MemoryRepository
from app.models.candidate_memory import MemorySummary


class MemorySummarizer:
    """Summarizes and compresses candidate interview memories."""

    def __init__(self, db: Session) -> None:
        self.repo = MemoryRepository(db)

    def summarize_candidate_memories(self, candidate_id: str) -> MemorySummary:
        """
        Compress candidate interview memories into a single MemorySummary.
        """
        memories = self.repo.list_memories(candidate_id, limit=50)
        skills = self.repo.list_skill_progress(candidate_id)

        if not memories:
            return self.repo.create_summary(
                candidate_id=candidate_id,
                compressed_summary="Candidate has no recorded interview memories yet.",
                interview_count_covered=0,
                key_strengths=[],
                key_weaknesses=[],
            )

        strengths = [s.skill_name for s in skills if s.current_score >= 80.0]
        weaknesses = [s.skill_name for s in skills if s.current_score < 60.0]

        topics_seen = set()
        summaries_text = []

        for idx, m in enumerate(memories, 1):
            summaries_text.append(f"Interview {idx}: {m.summary}")
            for t in m.get_topics():
                topics_seen.add(t)

        compressed = (
            f"Candidate evaluated across {len(memories)} interview sessions. "
            f"Key topics covered: {', '.join(sorted(topics_seen)) if topics_seen else 'General Technical'}. "
            f"Overall performance demonstrates solid progress in {', '.join(strengths) if strengths else 'core fundamentals'}, "
            f"with active improvement areas in {', '.join(weaknesses) if weaknesses else 'advanced architectural concepts'}."
        )

        # Update profile summary
        self.repo.update_profile(
            candidate_id=candidate_id,
            strengths=strengths,
            weaknesses=weaknesses,
            summary=compressed,
        )

        return self.repo.create_summary(
            candidate_id=candidate_id,
            compressed_summary=compressed,
            interview_count_covered=len(memories),
            key_strengths=strengths,
            key_weaknesses=weaknesses,
        )
