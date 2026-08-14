"""0007_career_intelligence_engine

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-05 21:50:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Adaptive Sessions
    op.create_table(
        "adaptive_sessions",
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
        sa.Column("current_difficulty", sa.Float(), nullable=False, server_default="5.0"),
        sa.Column("target_difficulty", sa.Float(), nullable=False, server_default="5.0"),
        sa.Column("consecutive_correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_incorrect", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_adaptive_sessions_interview_id", "adaptive_sessions", ["interview_id"])
    op.create_index("ix_adaptive_sessions_candidate_id", "adaptive_sessions", ["candidate_id"])

    # 2. Difficulty History
    op.create_table(
        "difficulty_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "session_id",
            sa.String(length=36),
            sa.ForeignKey("adaptive_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_number", sa.Integer(), nullable=False),
        sa.Column("difficulty_assigned", sa.Float(), nullable=False),
        sa.Column("performance_score", sa.Float(), nullable=False),
        sa.Column("response_latency_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("adjustment_reason", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_difficulty_history_session_id", "difficulty_history", ["session_id"])

    # 3. Company Profiles
    op.create_table(
        "company_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("company_name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("coding_weight", sa.Float(), nullable=False, server_default="0.35"),
        sa.Column("system_design_weight", sa.Float(), nullable=False, server_default="0.35"),
        sa.Column("behavioral_weight", sa.Float(), nullable=False, server_default="0.30"),
        sa.Column("key_principles", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_name"),
    )
    op.create_index("ix_company_profiles_company_name", "company_profiles", ["company_name"])

    # 4. Industry Benchmarks
    op.create_table(
        "industry_benchmarks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("average_score", sa.Float(), nullable=False, server_default="68.0"),
        sa.Column("top_10_percentile_score", sa.Float(), nullable=False, server_default="91.0"),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_industry_benchmarks_category", "industry_benchmarks", ["category"])

    # 5. Candidate Predictions
    op.create_table(
        "candidate_predictions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "candidate_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("hire_probability", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("outcome", sa.String(length=20), nullable=False),
        sa.Column("key_reasons", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_candidate_predictions_candidate_id", "candidate_predictions", ["candidate_id"]
    )

    # 6. Skill Gap Analysis
    op.create_table(
        "skill_gap_analysis",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "candidate_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic", sa.String(length=100), nullable=False),
        sa.Column("missing_concepts", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="HIGH"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_skill_gap_analysis_candidate_id", "skill_gap_analysis", ["candidate_id"])

    # 7. Career Roadmaps
    op.create_table(
        "career_roadmaps",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "candidate_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("daily_plan", sa.Text(), nullable=False),
        sa.Column("weekly_plan", sa.Text(), nullable=False),
        sa.Column("monthly_plan", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_roadmaps_candidate_id", "career_roadmaps", ["candidate_id"])

    # 8. Interview Annotations
    op.create_table(
        "interview_annotations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "interview_id",
            sa.String(length=36),
            sa.ForeignKey("interviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timestamp_mark", sa.String(length=20), nullable=False),
        sa.Column("annotation_type", sa.String(length=50), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_interview_annotations_interview_id", "interview_annotations", ["interview_id"]
    )

    # 9. Knowledge Graph Nodes & Edges
    op.create_table(
        "knowledge_graph_nodes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("node_type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("properties_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_graph_nodes_node_type", "knowledge_graph_nodes", ["node_type"])

    op.create_table(
        "knowledge_graph_edges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "source_id",
            sa.String(length=36),
            sa.ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_id",
            sa.String(length=36),
            sa.ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relation_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_graph_edges_source_id", "knowledge_graph_edges", ["source_id"])
    op.create_index("ix_knowledge_graph_edges_target_id", "knowledge_graph_edges", ["target_id"])
    op.create_index(
        "ix_knowledge_graph_edges_relation_type", "knowledge_graph_edges", ["relation_type"]
    )


def downgrade() -> None:
    op.drop_table("knowledge_graph_edges")
    op.drop_table("knowledge_graph_nodes")
    op.drop_table("interview_annotations")
    op.drop_table("career_roadmaps")
    op.drop_table("skill_gap_analysis")
    op.drop_table("candidate_predictions")
    op.drop_table("industry_benchmarks")
    op.drop_table("company_profiles")
    op.drop_table("difficulty_history")
    op.drop_table("adaptive_sessions")
