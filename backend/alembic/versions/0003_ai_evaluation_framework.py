"""0003_ai_evaluation_framework

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-05 18:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Evaluation Runs Table
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False, server_default="v1"),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column(
            "dataset_name", sa.String(length=100), nullable=False, server_default="golden_dataset"
        ),
        sa.Column("total_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passed_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_samples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_correctness", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_faithfulness", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_hallucination", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_relevancy", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("pass_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evaluation_runs_run_name", "evaluation_runs", ["run_name"])

    # 2. Evaluation Results Table
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("sample_id", sa.String(length=100), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("candidate_answer", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=True),
        sa.Column("correctness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("faithfulness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("hallucination_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("relevancy_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evaluation_results_sample_id", "evaluation_results", ["sample_id"])

    # 3. Benchmark Results Table
    op.create_table(
        "benchmark_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("benchmark_name", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False, server_default="v1"),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("latency_p95_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_benchmark_results_benchmark_name", "benchmark_results", ["benchmark_name"])

    # 4. Prompt Scores Table
    op.create_table(
        "prompt_scores",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("prompt_key", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("average_accuracy", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("average_latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("average_cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_evaluations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prompt_scores_prompt_key", "prompt_scores", ["prompt_key"])

    # 5. Model Scores Table
    op.create_table(
        "model_scores",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider_name", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("accuracy_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("latency_p95_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("cost_per_1k_tokens", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("quality_rating", sa.String(length=20), nullable=False, server_default="STRONG"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_model_scores_model_name", "model_scores", ["model_name"])


def downgrade() -> None:
    op.drop_index("ix_model_scores_model_name", table_name="model_scores")
    op.drop_table("model_scores")
    op.drop_index("ix_prompt_scores_prompt_key", table_name="prompt_scores")
    op.drop_table("prompt_scores")
    op.drop_index("ix_benchmark_results_benchmark_name", table_name="benchmark_results")
    op.drop_table("benchmark_results")
    op.drop_index("ix_evaluation_results_sample_id", table_name="evaluation_results")
    op.drop_table("evaluation_results")
    op.drop_index("ix_evaluation_runs_run_name", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
