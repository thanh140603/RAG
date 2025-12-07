"""add_document_groups

Revision ID: b2eb0d5becaa
Revises: 9b5cfe93e825
Create Date: 2025-11-29 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2eb0d5becaa'
down_revision = '9b5cfe93e825'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create document_groups table (if not exists)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    if 'document_groups' not in tables:
        op.create_table(
            'document_groups',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('color', sa.String(length=7), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )
        op.create_index('ix_document_groups_user_id', 'document_groups', ['user_id'], unique=False)
    
    # Add group_id to documents table (if not exists)
    columns = [col['name'] for col in inspector.get_columns('documents')]
    if 'group_id' not in columns:
        op.add_column('documents', sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            'fk_documents_group_id',
            'documents',
            'document_groups',
            ['group_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_index('ix_documents_group_id', 'documents', ['group_id'], unique=False)


def downgrade() -> None:
    # Remove group_id from documents
    op.drop_index('ix_documents_group_id', table_name='documents')
    op.drop_constraint('fk_documents_group_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'group_id')
    
    # Drop document_groups table
    op.drop_index('ix_document_groups_user_id', table_name='document_groups')
    op.drop_table('document_groups')
