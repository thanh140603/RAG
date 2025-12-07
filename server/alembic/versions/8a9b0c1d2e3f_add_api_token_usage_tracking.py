"""add_api_token_usage_tracking

Revision ID: 8a9b0c1d2e3f
Revises: 3a79b1af5eef
Create Date: 2024-12-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8a9b0c1d2e3f'
down_revision: Union[str, None] = '3a79b1af5eef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    if 'api_token_usage' not in tables:
        # Create api_token_usage table
        op.create_table(
            'api_token_usage',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('provider', sa.String(50), nullable=False),
            sa.Column('date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('requests_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('daily_limit', sa.Integer(), nullable=True),
            sa.Column('monthly_limit', sa.Integer(), nullable=True),
            sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    
    # Check and create indexes
    indexes = [idx['name'] for idx in inspector.get_indexes('api_token_usage')] if 'api_token_usage' in tables else []
    
    if 'ix_api_token_usage_provider' not in indexes:
        op.create_index('ix_api_token_usage_provider', 'api_token_usage', ['provider'])
    if 'ix_api_token_usage_date' not in indexes:
        op.create_index('ix_api_token_usage_date', 'api_token_usage', ['date'])
    if 'ix_api_token_usage_provider_date' not in indexes:
        op.create_index('ix_api_token_usage_provider_date', 'api_token_usage', ['provider', 'date'])
    
    # Check and create unique constraint
    constraints = [c['name'] for c in inspector.get_unique_constraints('api_token_usage')] if 'api_token_usage' in tables else []
    if 'uq_api_token_usage_provider_date' not in constraints:
        op.create_unique_constraint('uq_api_token_usage_provider_date', 'api_token_usage', ['provider', 'date'])


def downgrade() -> None:
    op.drop_constraint('uq_api_token_usage_provider_date', 'api_token_usage', type_='unique')
    op.drop_index('ix_api_token_usage_provider_date', table_name='api_token_usage')
    op.drop_index('ix_api_token_usage_date', table_name='api_token_usage')
    op.drop_index('ix_api_token_usage_provider', table_name='api_token_usage')
    op.drop_table('api_token_usage')

