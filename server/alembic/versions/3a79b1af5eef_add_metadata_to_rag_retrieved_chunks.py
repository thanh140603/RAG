"""add_metadata_to_rag_retrieved_chunks

Revision ID: 3a79b1af5eef
Revises: 7f3a9c2b8f4a
Create Date: 2025-12-05 02:36:43.663455

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3a79b1af5eef'
down_revision = '7f3a9c2b8f4a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add metadata column (JSONB) to rag_retrieved_chunks table
    op.add_column(
        'rag_retrieved_chunks',
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='{}')
    )


def downgrade() -> None:
    # Remove metadata column
    op.drop_column('rag_retrieved_chunks', 'metadata')