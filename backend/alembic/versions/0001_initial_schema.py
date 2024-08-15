"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-10
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op
from app.db.types import EmbeddingType

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIM = 256


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "notebooks",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "owner_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(7), nullable=False, server_default="#6366f1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_id", "name", name="uq_notebook_owner_name"),
    )
    op.create_index("ix_notebooks_owner_id", "notebooks", ["owner_id"])

    op.create_table(
        "tags",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "owner_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(50), nullable=False),
        sa.UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),
    )
    op.create_index("ix_tags_owner_id", "tags", ["owner_id"])

    op.create_table(
        "notes",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "owner_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "notebook_id",
            sa.String(32),
            sa.ForeignKey("notebooks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("embedding", EmbeddingType(EMBEDDING_DIM), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notes_owner_id", "notes", ["owner_id"])
    op.create_index("ix_notes_notebook_id", "notes", ["notebook_id"])
    op.create_index("ix_notes_owner_updated", "notes", ["owner_id", "updated_at"])
    op.create_index("ix_notes_owner_deleted", "notes", ["owner_id", "is_deleted"])
    if is_postgres:
        op.execute(
            "CREATE INDEX ix_notes_embedding_cosine ON notes "
            "USING hnsw (embedding vector_cosine_ops)"
        )
        op.execute(
            "CREATE INDEX ix_notes_fts ON notes USING gin "
            "(to_tsvector('english', title || ' ' || content || ' ' || coalesce(summary, '')))"
        )

    op.create_table(
        "note_tags",
        sa.Column(
            "note_id",
            sa.String(32),
            sa.ForeignKey("notes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id", sa.String(32), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
        ),
    )

    op.create_table(
        "note_versions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "note_id", sa.String(32), sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("note_id", "version", name="uq_note_version"),
    )
    op.create_index("ix_note_versions_note_id", "note_versions", ["note_id"])

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "owner_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chat_sessions_owner_id", "chat_sessions", ["owner_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(32),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id", sa.String(32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    for table in (
        "refresh_tokens",
        "chat_messages",
        "chat_sessions",
        "note_versions",
        "note_tags",
        "notes",
        "tags",
        "notebooks",
        "users",
    ):
        op.drop_table(table)
