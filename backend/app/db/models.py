"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin, as_utc, new_id, utcnow
from app.db.types import EmbeddingType

EMBEDDING_DIM = 256

note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", String(32), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(32), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(IdMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    notebooks: Mapped[list[Notebook]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    notes: Mapped[list[Note]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Notebook(IdMixin, TimestampMixin, Base):
    __tablename__ = "notebooks"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_notebook_owner_name"),)

    owner_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#6366f1", nullable=False)

    owner: Mapped[User] = relationship(back_populates="notebooks")
    notes: Mapped[list[Note]] = relationship(back_populates="notebook")


class Tag(IdMixin, Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),)

    owner_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    notes: Mapped[list[Note]] = relationship(secondary=note_tags, back_populates="tag_links")


class Note(IdMixin, TimestampMixin, Base):
    __tablename__ = "notes"
    __table_args__ = (
        Index("ix_notes_owner_updated", "owner_id", "updated_at"),
        Index("ix_notes_owner_deleted", "owner_id", "is_deleted"),
    )

    owner_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    notebook_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("notebooks.id", ondelete="SET NULL"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        EmbeddingType(EMBEDDING_DIM), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped[User] = relationship(back_populates="notes")
    notebook: Mapped[Notebook | None] = relationship(back_populates="notes")
    tag_links: Mapped[list[Tag]] = relationship(secondary=note_tags, back_populates="notes")
    versions: Mapped[list[NoteVersion]] = relationship(
        back_populates="note", cascade="all, delete-orphan", order_by="NoteVersion.version.desc()"
    )


class NoteVersion(IdMixin, Base):
    __tablename__ = "note_versions"
    __table_args__ = (UniqueConstraint("note_id", "version", name="uq_note_version"),)

    note_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("notes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    note: Mapped[Note] = relationship(back_populates="versions")


class ChatSession(IdMixin, TimestampMixin, Base):
    __tablename__ = "chat_sessions"

    owner_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), default="New conversation", nullable=False)

    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(IdMixin, Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)  # == jti
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and as_utc(self.expires_at) > utcnow()
