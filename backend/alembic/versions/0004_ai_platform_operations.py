"""0004_ai_platform_operations

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-05 18:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Review Queue Table
    op.create_table(
        "review_queue",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("response_id", sa.String(length=100), nullable=True),
        sa.Column("interview_id", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("assigned_admin", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_review_queue_interview_id", "review_queue", ["interview_id"])
    op.create_index("ix_review_queue_status", "review_queue", ["status"])

    # 2. Recruiter Feedbacks Table
    op.create_table(
        "recruiter_feedbacks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("interview_id", sa.String(length=100), nullable=False),
        sa.Column("question_id", sa.String(length=100), nullable=True),
        sa.Column("recruiter_id", sa.String(length=100), nullable=False),
        sa.Column("rating_action", sa.String(length=50), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recruiter_feedbacks_interview_id", "recruiter_feedbacks", ["interview_id"])
    op.create_index("ix_recruiter_feedbacks_recruiter_id", "recruiter_feedbacks", ["recruiter_id"])


def downgrade() -> None:
    op.drop_index("ix_recruiter_feedbacks_recruiter_id", table_name="recruiter_feedbacks")
    op.drop_index("ix_recruiter_feedbacks_interview_id", table_name="recruiter_feedbacks")
    op.drop_table("recruiter_feedbacks")
    op.drop_index("ix_review_queue_status", table_name="review_queue")
    op.drop_index("ix_review_queue_interview_id", table_name="review_queue")
    op.drop_table("review_queue")
