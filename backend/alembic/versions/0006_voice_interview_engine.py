"""0006_voice_interview_engine

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-05 21:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Live Sessions
    op.create_table(
        "live_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "interview_id",
            sa.String(length=36),
            sa.ForeignKey("interviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "active_worker_id", sa.String(length=50), nullable=False, server_default="worker-01"
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_live_sessions_interview_id", "live_sessions", ["interview_id"])
    op.create_index("ix_live_sessions_candidate_id", "live_sessions", ["candidate_id"])
    op.create_index("ix_live_sessions_status", "live_sessions", ["status"])

    # 2. Conversation Turns
    op.create_table(
        "conversation_turns",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "session_id",
            sa.String(length=36),
            sa.ForeignKey("live_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("turn_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("speaker", sa.String(length=50), nullable=False, server_default="CANDIDATE"),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "agent_name",
            sa.String(length=100),
            nullable=False,
            server_default="TechnicalInterviewAgent",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversation_turns_session_id", "conversation_turns", ["session_id"])

    # 3. Voice Metrics
    op.create_table(
        "voice_metrics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "session_id",
            sa.String(length=36),
            sa.ForeignKey("live_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("avg_speaking_speed_wpm", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_speaking_time_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "total_silence_duration_seconds", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("answer_latency_avg_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_words_spoken", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("technical_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("communication_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("confidence_estimate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("ix_voice_metrics_session_id", "voice_metrics", ["session_id"])
    op.create_index("ix_voice_metrics_candidate_id", "voice_metrics", ["candidate_id"])

    # 4. Speech Events
    op.create_table(
        "speech_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "session_id",
            sa.String(length=36),
            sa.ForeignKey("live_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("payload_summary", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_speech_events_session_id", "speech_events", ["session_id"])

    # 5. Transcripts Export Table
    op.create_table(
        "transcripts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "interview_id",
            sa.String(length=36),
            sa.ForeignKey("interviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.String(length=36),
            sa.ForeignKey("live_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("turn_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_path", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transcripts_interview_id", "transcripts", ["interview_id"])
    op.create_index("ix_transcripts_session_id", "transcripts", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_transcripts_session_id", table_name="transcripts")
    op.drop_index("ix_transcripts_interview_id", table_name="transcripts")
    op.drop_table("transcripts")
    op.drop_index("ix_speech_events_session_id", table_name="speech_events")
    op.drop_table("speech_events")
    op.drop_index("ix_voice_metrics_candidate_id", table_name="voice_metrics")
    op.drop_index("ix_voice_metrics_session_id", table_name="voice_metrics")
    op.drop_table("voice_metrics")
    op.drop_index("ix_conversation_turns_session_id", table_name="conversation_turns")
    op.drop_table("conversation_turns")
    op.drop_index("ix_live_sessions_status", table_name="live_sessions")
    op.drop_index("ix_live_sessions_candidate_id", table_name="live_sessions")
    op.drop_index("ix_live_sessions_interview_id", table_name="live_sessions")
    op.drop_table("live_sessions")
