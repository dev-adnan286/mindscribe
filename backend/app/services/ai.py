"""AI features: summaries, tag suggestions and retrieval-augmented chat with citations."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import get_embedder, get_provider
from app.ai.providers.base import ContextNote, LLMProvider
from app.ai.text import truncate
from app.core.config import get_settings
from app.core.deps import require_owner
from app.core.exceptions import NotFoundError
from app.db.base import utcnow
from app.db.models import ChatSession, Note, User
from app.repositories.chat import ChatRepository
from app.schemas.ai import (
    AIStatus,
    SummarizeRequest,
    SummarizeResponse,
    TagSuggestRequest,
    TagSuggestResponse,
)
from app.schemas.chat import (
    AskRequest,
    AskResponse,
    ChatMessageRead,
    ChatSessionRead,
    Citation,
)
from app.schemas.notes import normalise_tags
from app.services.notes import NoteService
from app.services.search import SearchService


class AIService:
    def __init__(self, db: AsyncSession, provider: LLMProvider | None = None) -> None:
        self.db = db
        self.provider = provider or get_provider()
        self.notes = NoteService(db)
        self.search = SearchService(db)
        self.chat = ChatRepository(db)

    def status(self) -> AIStatus:
        settings = get_settings()
        embedder = get_embedder()
        return AIStatus(
            provider=self.provider.name,
            model=self.provider.model,
            embedding_provider=embedder.name,
            embedding_dim=settings.embedding_dim,
        )

    async def _resolve_text(
        self, note_id: str | None, content: str | None, user: User
    ) -> tuple[Note | None, str]:
        if note_id:
            note = await self.notes.get_owned(note_id, user)
            return note, f"{note.title}\n\n{note.content}"
        return None, content or ""

    async def summarize(self, data: SummarizeRequest, user: User) -> SummarizeResponse:
        note, text = await self._resolve_text(data.note_id, data.content, user)
        summary = await self.provider.summarize(text, max_sentences=data.max_sentences)
        applied = False
        if data.apply and note is not None:
            await self.notes.apply_summary(note.id, summary, user)
            applied = True
        return SummarizeResponse(
            note_id=note.id if note else None,
            summary=summary,
            provider=self.provider.name,
            applied=applied,
        )

    async def suggest_tags(self, data: TagSuggestRequest, user: User) -> TagSuggestResponse:
        note, text = await self._resolve_text(data.note_id, data.content, user)
        raw = await self.provider.generate_tags(text, max_tags=data.max_tags)
        try:
            tags = normalise_tags(raw)
        except ValueError:
            tags = [t for t in raw if t.replace("-", "").isalnum()][: data.max_tags]
        applied = False
        if data.apply and note is not None:
            await self.notes.apply_tags(note.id, tags, user)
            applied = True
        return TagSuggestResponse(
            note_id=note.id if note else None,
            tags=tags,
            provider=self.provider.name,
            applied=applied,
        )

    # ---- chat -------------------------------------------------------------------------

    async def _get_owned_session(self, session_id: str, user: User) -> ChatSession:
        session = await self.chat.get_session(session_id)
        if session is None:
            raise NotFoundError("Chat session not found")
        require_owner(session.owner_id, user, "chat session")
        return session

    async def ask(self, data: AskRequest, user: User) -> AskResponse:
        if data.session_id:
            session = await self._get_owned_session(data.session_id, user)
        else:
            session = await self.chat.create_session(user.id, truncate(data.question, 80))

        history_msgs = await self.chat.list_messages(session.id)
        history = [(m.role, m.content) for m in history_msgs]

        ranked, _engine = await self.search.semantic(
            user, data.question, data.top_k, data.notebook_id
        )
        contexts = [
            ContextNote(
                index=i + 1,
                note_id=note.id,
                title=note.title,
                content=note.content,
                score=max(0.0, min(1.0, score)),
            )
            for i, (note, score) in enumerate(ranked)
        ]
        answer = await self.provider.answer(data.question, contexts, history)

        cited_indexes = {ctx.index for ctx in contexts if f"[{ctx.index}]" in answer}
        citations = [
            Citation(
                index=ctx.index,
                note_id=ctx.note_id,
                title=ctx.title,
                snippet=truncate(ctx.content, 140),
                score=round(ctx.score, 4),
            )
            for ctx in contexts
            if not cited_indexes or ctx.index in cited_indexes
        ]

        user_msg = await self.chat.add_message(session, "user", data.question)
        assistant_msg = await self.chat.add_message(
            session, "assistant", answer, [c.model_dump() for c in citations]
        )
        session.updated_at = utcnow()
        await self.db.flush()
        return AskResponse(
            session_id=session.id,
            user_message=ChatMessageRead.model_validate(user_msg),
            assistant_message=ChatMessageRead.model_validate(assistant_msg),
            provider=self.provider.name,
        )

    async def list_sessions(self, user: User) -> list[ChatSessionRead]:
        rows = await self.chat.list_sessions(user.id)
        result: list[ChatSessionRead] = []
        for session, count in rows:
            read = ChatSessionRead.model_validate(session)
            read.message_count = count
            result.append(read)
        return result

    async def list_messages(self, session_id: str, user: User) -> list[ChatMessageRead]:
        session = await self._get_owned_session(session_id, user)
        return [
            ChatMessageRead.model_validate(m) for m in await self.chat.list_messages(session.id)
        ]

    async def delete_session(self, session_id: str, user: User) -> None:
        session = await self._get_owned_session(session_id, user)
        await self.chat.delete_session(session)
