"""0005_candidate_memory_engine

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-05 21:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Candidate Profiles
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "candidate_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("experience_years", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skills", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("current_level", sa.String(length=50), nullable=False, server_default="MID"),
        sa.Column("strengths", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("weaknesses", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id"),
    )
    op.create_index("ix_candidate_profiles_candidate_id", "candidate_profiles", ["candidate_id"])

    # 2. Candidate Memories
    op.create_table(
        "candidate_memories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "candidate_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "interview_id",
            sa.String(length=36),
            sa.ForeignKey("interviews.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("memory_type", sa.String(length=50), nullable=False, server_default="EPISODIC"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("key_topics", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_memories_candidate_id", "candidate_memories", ["candidate_id"])
    op.create_index("ix_candidate_memories_interview_id", "candidate_memories", ["interview_id"])

    # 3. Skill Progress
    op.create_table(
        "skill_progress",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "candidate_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_name", sa.String(length=100), nullable=False),
        sa.Column("current_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("best_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("average_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("trend", sa.String(length=20), nullable=False, server_default="STABLE"),
        sa.Column("total_evaluations", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "skill_name", name="uq_candidate_skill"),
    )
    op.create_index("ix_skill_progress_candidate_id", "skill_progress", ["candidate_id"])
    op.create_index("ix_skill_progress_skill_name", "skill_progress", ["skill_name"])

    # 4. Learning Recommendations
    op.create_table(
        "learning_recommendations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "candidate_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "interview_id",
            sa.String(length=36),
            sa.ForeignKey("interviews.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("target_topic", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="MEDIUM"),
        sa.Column("suggested_action", sa.Text(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_learning_recommendations_candidate_id", "learning_recommendations", ["candidate_id"]
    )

    # 5. Memory Summaries
    op.create_table(
        "memory_summaries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "candidate_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("compressed_summary", sa.Text(), nullable=False),
        sa.Column("interview_count_covered", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("key_strengths", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("key_weaknesses", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memory_summaries_candidate_id", "memory_summaries", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_memory_summaries_candidate_id", table_name="memory_summaries")
    op.drop_table("memory_summaries")
    op.drop_index("ix_learning_recommendations_candidate_id", table_name="learning_recommendations")
    op.drop_table("learning_recommendations")
    op.drop_index("ix_skill_progress_skill_name", table_name="skill_progress")
    op.drop_index("ix_skill_progress_candidate_id", table_name="skill_progress")
    op.drop_table("skill_progress")
    op.drop_index("ix_candidate_memories_interview_id", table_name="candidate_memories")
    op.drop_index("ix_candidate_memories_candidate_id", table_name="candidate_memories")
    op.drop_table("candidate_memories")
    op.drop_index("ix_candidate_profiles_candidate_id", table_name="candidate_profiles")
    op.drop_table("candidate_profiles")
