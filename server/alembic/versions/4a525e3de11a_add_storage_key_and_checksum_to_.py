"""add_storage_key_and_checksum_to_documents

Revision ID: 4a525e3de11a
Revises: b2eb0d5becaa
Create Date: 2025-11-29 17:01:52.309282

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a525e3de11a'
down_revision = 'b2eb0d5becaa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add storage_key and checksum columns to documents table
    op.add_column('documents', sa.Column('storage_key', sa.String(length=500), nullable=True))
    op.add_column('documents', sa.Column('checksum', sa.String(length=64), nullable=True))


def downgrade() -> None:
    # Remove storage_key and checksum columns from documents table
    op.drop_column('documents', 'checksum')
    op.drop_column('documents', 'storage_key')