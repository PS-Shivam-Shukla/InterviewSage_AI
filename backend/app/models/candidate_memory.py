"""
Candidate Memory & Personalization ORM Models.
Tables:
- candidate_profiles: Candidate level, experience, strengths, weaknesses
- candidate_memories: Episodic, semantic, and summary memories per interview
- skill_progress: Longitudinal skill trend, scores, and tracking
- learning_recommendations: Personalized learning roadmap items
- memory_summaries: Compressed long-term interview summaries
"""

import json
from datetime import datetime, timezone
from typing import Any, List, Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class CandidateProfile(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "candidate_profiles"

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skills: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON list
    current_level: Mapped[str] = mapped_column(String(50), nullable=False, default="MID")
    strengths: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON list
    weaknesses: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON list
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def set_skills(self, skills_list: List[str]) -> None:
        self.skills = json.dumps(skills_list)

    def get_skills(self) -> List[str]:
        return json.loads(self.skills) if self.skills else []

    def set_strengths(self, strengths_list: List[str]) -> None:
        self.strengths = json.dumps(strengths_list)

    def get_strengths(self) -> List[str]:
        return json.loads(self.strengths) if self.strengths else []

    def set_weaknesses(self, weaknesses_list: List[str]) -> None:
        self.weaknesses = json.dumps(weaknesses_list)

    def get_weaknesses(self) -> List[str]:
        return json.loads(self.weaknesses) if self.weaknesses else []

    def __repr__(self) -> str:
        return f"<CandidateProfile id={self.id!r} candidate_id={self.candidate_id!r} level={self.current_level}>"


class CandidateMemory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "candidate_memories"

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    interview_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    # EPISODIC | SEMANTIC | SUMMARY
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False, default="EPISODIC")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_topics: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON list
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of floats

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def set_topics(self, topics: List[str]) -> None:
        self.key_topics = json.dumps(topics)

    def get_topics(self) -> List[str]:
        return json.loads(self.key_topics) if self.key_topics else []

    def __repr__(self) -> str:
        return f"<CandidateMemory id={self.id!r} type={self.memory_type} candidate_id={self.candidate_id!r}>"


class SkillProgress(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "skill_progress"
    __table_args__ = (
        UniqueConstraint("candidate_id", "skill_name", name="uq_candidate_skill"),
    )

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    current_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    best_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # IMPROVING | REGRESSING | STABLE
    trend: Mapped[str] = mapped_column(String(20), nullable=False, default="STABLE")
    total_evaluations: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SkillProgress skill={self.skill_name!r} score={self.current_score} trend={self.trend}>"


class LearningRecommendation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_recommendations"

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    interview_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="SET NULL"),
        nullable=True
    )
    target_topic: Mapped[str] = mapped_column(String(100), nullable=False)
    # HIGH | MEDIUM | LOW
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM")
    suggested_action: Mapped[str] = mapped_column(Text, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<LearningRecommendation topic={self.target_topic!r} week={self.week_number}>"


class MemorySummary(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "memory_summaries"

    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    compressed_summary: Mapped[str] = mapped_column(Text, nullable=False)
    interview_count_covered: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    key_strengths: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON list
    key_weaknesses: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON list

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<MemorySummary candidate_id={self.candidate_id!r} covered={self.interview_count_covered}>"
