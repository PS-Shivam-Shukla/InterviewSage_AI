"""Initial schema — all tables

Revision ID: 0001
Revises: 
Create Date: 2026-08-03
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── resumes ────────────────────────────────────────────────────────────
    op.create_table(
        "resumes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("raw_text", sa.Text, nullable=False, default=""),
        sa.Column("parsed_skills", sa.Text, nullable=False, default="[]"),
        sa.Column("parsed_experience", sa.Text, nullable=False, default="[]"),
        sa.Column("seniority_signal", sa.String(50), nullable=False, default="UNKNOWN"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])

    # ── job_descriptions ───────────────────────────────────────────────────
    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("target_role", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("required_skills", sa.Text, nullable=False, default="[]"),
        sa.Column("seniority_level", sa.String(50), nullable=False, default="NOT_SPECIFIED"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_jd_user_id", "job_descriptions", ["user_id"])

    # ── interviews ─────────────────────────────────────────────────────────
    op.create_table(
        "interviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.String(36),
                  sa.ForeignKey("resumes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("jd_id", sa.String(36),
                  sa.ForeignKey("job_descriptions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="PLANNING"),
        sa.Column("current_round", sa.String(20), nullable=True),
        sa.Column("overall_score", sa.Integer, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interviews_user_id_status", "interviews", ["user_id", "status"])

    # ── competency_matrices ────────────────────────────────────────────────
    op.create_table(
        "competency_matrices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("interview_id", sa.String(36),
                  sa.ForeignKey("interviews.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("competencies", sa.Text, nullable=False, default="[]"),
    )

    # ── interview_plans ────────────────────────────────────────────────────
    op.create_table(
        "interview_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("interview_id", sa.String(36),
                  sa.ForeignKey("interviews.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("hr_question_count", sa.Integer, nullable=False, default=5),
        sa.Column("technical_question_count", sa.Integer, nullable=False, default=7),
        sa.Column("round_structure", sa.Text, nullable=False, default="{}"),
        sa.Column("estimated_duration_minutes", sa.Integer, nullable=False, default=60),
    )

    # ── interview_questions ────────────────────────────────────────────────
    op.create_table(
        "interview_questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("interview_id", sa.String(36),
                  sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("round_type", sa.String(20), nullable=False),
        sa.Column("competency_targeted", sa.String(255), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("sequence_number", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("interview_id", "sequence_number", name="uq_question_sequence"),
    )
    op.create_index("ix_questions_interview_id", "interview_questions", ["interview_id"])

    # ── interview_answers ──────────────────────────────────────────────────
    op.create_table(
        "interview_answers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("question_id", sa.String(36),
                  sa.ForeignKey("interview_questions.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("answer_text", sa.Text, nullable=False),
        sa.Column("response_time_seconds", sa.Integer, nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )

    # ── evaluations ────────────────────────────────────────────────────────
    op.create_table(
        "evaluations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("answer_id", sa.String(36),
                  sa.ForeignKey("interview_answers.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("rubric_breakdown", sa.Text, nullable=False, default="{}"),
        sa.Column("feedback", sa.Text, nullable=False, default=""),
        sa.Column("ideal_answer_summary", sa.Text, nullable=False, default=""),
    )

    # ── interview_reports ──────────────────────────────────────────────────
    op.create_table(
        "interview_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("interview_id", sa.String(36),
                  sa.ForeignKey("interviews.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("competency_scorecard", sa.Text, nullable=False, default="[]"),
        sa.Column("improvement_plan", sa.Text, nullable=False, default="[]"),
        sa.Column("transcript_snapshot", sa.Text, nullable=False, default="[]"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── agent_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "agent_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("interview_id", sa.String(36),
                  sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("node_status", sa.String(20), nullable=False),
        sa.Column("input_snapshot", sa.Text, nullable=False, default="{}"),
        sa.Column("output_snapshot", sa.Text, nullable=False, default="{}"),
        sa.Column("latency_ms", sa.Integer, nullable=False, default=0),
        sa.Column("retry_count", sa.Integer, nullable=False, default=0),
        sa.Column("prompt_version", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agent_logs_interview_created",
                    "agent_logs", ["interview_id", "created_at"])


def downgrade() -> None:
    op.drop_table("agent_logs")
    op.drop_table("interview_reports")
    op.drop_table("evaluations")
    op.drop_table("interview_answers")
    op.drop_table("interview_questions")
    op.drop_table("interview_plans")
    op.drop_table("competency_matrices")
    op.drop_table("interviews")
    op.drop_table("job_descriptions")
    op.drop_table("resumes")
    op.drop_table("users")
