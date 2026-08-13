"""0002_ai_platform_observability

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-05 18:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Prompt Versions Table
    op.create_table(
        'prompt_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('prompt_key', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False, server_default='v1'),
        sa.Column('system_template', sa.Text(), nullable=False),
        sa.Column('user_template', sa.Text(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_prompt_versions_prompt_key', 'prompt_versions', ['prompt_key'])
    op.create_index('ix_prompt_versions_is_active', 'prompt_versions', ['is_active'])

    # 2. LLM Requests Table
    op.create_table(
        'llm_requests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('interview_id', sa.String(length=100), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='ollama'),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False, server_default='general'),
        sa.Column('prompt_version', sa.String(length=20), nullable=True, server_default='v1'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_llm_requests_request_id', 'llm_requests', ['request_id'])
    op.create_index('ix_llm_requests_interview_id', 'llm_requests', ['interview_id'])

    # 3. LLM Responses Table
    op.create_table(
        'llm_responses',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('llm_request_id', sa.String(length=36), nullable=False),
        sa.Column('raw_output', sa.Text(), nullable=True),
        sa.Column('parsed_output', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('repair_performed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['llm_request_id'], ['llm_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Token Usages Table
    op.create_table(
        'token_usages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=True),
        sa.Column('interview_id', sa.String(length=100), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False, server_default='ollama'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_token_usages_user_id', 'token_usages', ['user_id'])
    op.create_index('ix_token_usages_interview_id', 'token_usages', ['interview_id'])


def downgrade() -> None:
    op.drop_index('ix_token_usages_interview_id', table_name='token_usages')
    op.drop_index('ix_token_usages_user_id', table_name='token_usages')
    op.drop_table('token_usages')
    op.drop_table('llm_responses')
    op.drop_index('ix_llm_requests_interview_id', table_name='llm_requests')
    op.drop_index('ix_llm_requests_request_id', table_name='llm_requests')
    op.drop_table('llm_requests')
    op.drop_index('ix_prompt_versions_is_active', table_name='prompt_versions')
    op.drop_index('ix_prompt_versions_prompt_key', table_name='prompt_versions')
    op.drop_table('prompt_versions')
