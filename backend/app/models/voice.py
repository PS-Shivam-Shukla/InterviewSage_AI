"""
Real-Time Voice Interview Engine ORM Models.
Tables:
- live_sessions: Real-time voice interview sessions
- conversation_turns: Turn-by-turn candidate & AI speaker logs
- voice_metrics: Deterministic voice analytics (speaking speed WPM, latency, silence)
- speech_events: Real-time streaming speech events
- transcripts: Consolidated transcript exports
"""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class LiveSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "live_sessions"

    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    # ACTIVE | PAUSED | COMPLETED | DISCONNECTED
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE", index=True)
    active_worker_id: Mapped[str] = mapped_column(String(50), nullable=False, default="worker-01")

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    turns: Mapped[list["ConversationTurn"]] = relationship("ConversationTurn", back_populates="session", cascade="all, delete-orphan")
    metrics: Mapped[Optional["VoiceMetrics"]] = relationship("VoiceMetrics", back_populates="session", uselist=False, cascade="all, delete-orphan")
    events: Mapped[list["SpeechEvent"]] = relationship("SpeechEvent", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<LiveSession id={self.id!r} interview_id={self.interview_id!r} status={self.status}>"


class ConversationTurn(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "conversation_turns"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("live_sessions.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # CANDIDATE | AI_AGENT | SYSTEM
    speaker: Mapped[str] = mapped_column(String(50), nullable=False, default="CANDIDATE")
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, default="TechnicalInterviewAgent")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    session: Mapped["LiveSession"] = relationship("LiveSession", back_populates="turns")

    def __repr__(self) -> str:
        return f"<ConversationTurn turn={self.turn_number} speaker={self.speaker}>"


class VoiceMetrics(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "voice_metrics"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("live_sessions.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    avg_speaking_speed_wpm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_speaking_time_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_silence_duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    answer_latency_avg_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_words_spoken: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    communication_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_estimate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    session: Mapped["LiveSession"] = relationship("LiveSession", back_populates="metrics")


class SpeechEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "speech_events"

    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("live_sessions.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    # CHUNK_RECEIVED | TRANSCRIPTION_COMPLETE | TTS_SYNTHESIZED | WEBSOCKET_DISCONNECT
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["LiveSession"] = relationship("LiveSession", back_populates="events")


class TranscriptExport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "transcripts"

    interview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("live_sessions.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
