"""add_model_column_to_embeddings

Revision ID: 7f3a9c2b8f4a
Revises: 4a525e3de11a
Create Date: 2025-12-01 17:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7f3a9c2b8f4a"
down_revision = "4a525e3de11a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Align embeddings table with SQLAlchemy model.

    - Add `model` column (required by EmbeddingModel)
    - Drop legacy `text` column (no longer used by code)
    """
    # Add `model` column as nullable first
    op.add_column(
        "embeddings",
        sa.Column("model", sa.String(length=100), nullable=True),
    )

    # Optionally backfill existing rows with a generic value
    op.execute(
        "UPDATE embeddings SET model = 'unknown' WHERE model IS NULL"
    )

    # Make column non-nullable to match model definition
    op.alter_column("embeddings", "model", nullable=False)

    # Drop legacy `text` column if it exists
    # (older schema had `text` column that is no longer present in the model)
    with op.batch_alter_table("embeddings") as batch_op:
        try:
            batch_op.drop_column("text")
        except Exception:
            # If the column was already dropped manually, ignore
            pass


def downgrade() -> None:
    """Revert embeddings table changes.

    - Recreate `text` column (without restoring data)
    - Drop `model` column
    """
    with op.batch_alter_table("embeddings") as batch_op:
        batch_op.add_column(
            sa.Column("text", sa.Text(), nullable=True)
        )
        batch_op.drop_column("model")


