"""
Initial database schema for RAG system.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "20231117_0001"
down_revision = None
branch_labels = None
depends_on = None


document_status_enum = sa.Enum(
    "pending", "processing", "indexed", "error", name="document_status"
)
rag_query_status_enum = sa.Enum(
    "pending", "completed", "failed", name="rag_query_status"
)


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    bind = op.get_bind()
    document_status_enum.create(bind, checkfirst=True)
    rag_query_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("status", document_status_enum, nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("chunk_count", sa.Integer, nullable=True),
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("start_offset", sa.Integer, nullable=True),
        sa.Column("end_offset", sa.Integer, nullable=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("document_id", "order", name="uq_chunk_document_order"),
    )

    op.create_table(
        "embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chunks.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("vector", Vector(1536), nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "chat_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "rag_queries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "chat_message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_messages.id", ondelete="SET NULL"),
            nullable=True,
            unique=True,
        ),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column("translated_query", sa.Text, nullable=True),
        sa.Column("step_back_query", sa.Text, nullable=True),
        sa.Column("options", postgresql.JSONB, nullable=True),
        sa.Column("use_multi_query", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("use_step_back", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("top_k", sa.Integer, nullable=False, server_default="5"),
        sa.Column("status", rag_query_status_enum, nullable=False),
        sa.Column("response_latency_ms", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "rag_retrieved_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rag_query_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rag_queries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chunks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("rag_query_id", "chunk_id", name="uq_rag_query_chunk"),
    )

    # Indexes
    op.create_index("ix_documents_user_id", "documents", ["user_id"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.create_index("ix_chunks_order", "chunks", ["order"])
    op.create_index("ix_embeddings_document_id", "embeddings", ["document_id"])
    op.create_index(
        "idx_embedding_vector",
        "embeddings",
        ["vector"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 100},
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["chat_session_id"])
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])
    op.create_index("ix_rag_queries_user_id", "rag_queries", ["user_id"])
    op.create_index("ix_rag_queries_message_id", "rag_queries", ["chat_message_id"])
    op.create_index(
        "ix_rag_retrieved_query_id", "rag_retrieved_chunks", ["rag_query_id"]
    )
    op.create_index("ix_rag_retrieved_chunk_id", "rag_retrieved_chunks", ["chunk_id"])
    op.create_index(
        "idx_rag_query_rank",
        "rag_retrieved_chunks",
        ["rag_query_id", "rank"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_rag_query_rank", table_name="rag_retrieved_chunks")
    op.drop_index("ix_rag_retrieved_chunk_id", table_name="rag_retrieved_chunks")
    op.drop_index("ix_rag_retrieved_query_id", table_name="rag_retrieved_chunks")
    op.drop_index("ix_rag_queries_message_id", table_name="rag_queries")
    op.drop_index("ix_rag_queries_user_id", table_name="rag_queries")
    op.drop_index("ix_chat_messages_created_at", table_name="chat_messages")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_index("ix_chat_sessions_user_id", table_name="chat_sessions")
    op.drop_index("idx_embedding_vector", table_name="embeddings")
    op.drop_index("ix_embeddings_document_id", table_name="embeddings")
    op.drop_index("ix_chunks_order", table_name="chunks")
    op.drop_index("ix_chunks_document_id", table_name="chunks")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_user_id", table_name="documents")

    # Drop tables in reverse order
    op.drop_table("rag_retrieved_chunks")
    op.drop_table("rag_queries")
    op.drop_table("chat_messages")
    op.drop_table("embeddings")
    op.drop_table("chunks")
    op.drop_table("chat_sessions")
    op.drop_table("documents")
    op.drop_table("users")

    bind = op.get_bind()
    rag_query_status_enum.drop(bind, checkfirst=True)
    document_status_enum.drop(bind, checkfirst=True)

