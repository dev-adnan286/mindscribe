"""Seed the database with a demo user, notebooks and sample notes.

Usage (from backend/):  python -m scripts.seed
Login afterwards with demo@mindscribe.dev / Password123
"""

from __future__ import annotations

import asyncio
import sys

from app.core.logging import configure_logging, get_logger
from app.db.session import create_engine, create_session_factory, init_db
from app.repositories.users import UserRepository
from app.schemas.notebooks import NotebookCreate
from app.schemas.notes import NoteCreate
from app.services.auth import AuthService
from app.services.notebooks import NotebookService
from app.services.notes import NoteService

log = get_logger("seed")

DEMO_EMAIL = "demo@mindscribe.dev"
DEMO_PASSWORD = "Password123"

NOTEBOOKS = [
    ("Engineering", "Architecture notes, incident write-ups and design docs", "#6366f1"),
    ("Reading", "Highlights and takeaways from books and articles", "#10b981"),
    ("Personal", "Plans, journals and ideas", "#f59e0b"),
]

NOTES: list[tuple[str, str, str, list[str]]] = [
    (
        "Engineering",
        "Event-driven architecture notes",
        """# Event-driven architecture

Services communicate by publishing events to a broker instead of calling each other
directly. This decouples producers from consumers and lets each service scale on its own.

Key ideas:
- Events are immutable facts about something that happened.
- Consumers must be idempotent because delivery is at-least-once.
- Use an outbox table to publish events atomically with database writes.

Trade-offs: eventual consistency makes debugging harder, so invest early in tracing and
a schema registry for event contracts.""",
        ["architecture", "events", "distributed-systems"],
    ),
    (
        "Engineering",
        "Postgres performance checklist",
        """Before optimising a slow query, run EXPLAIN ANALYZE and look at the actual rows
versus the estimated rows. Large differences mean stale statistics - run ANALYZE.

Checklist:
1. Add indexes for columns in WHERE and JOIN clauses, but avoid over-indexing writes.
2. Prefer covering indexes for hot read paths.
3. Keep connection pools small; Postgres processes are expensive.
4. Use pgvector HNSW indexes for approximate nearest neighbour search on embeddings.

Vacuum regularly so dead tuples do not bloat tables.""",
        ["postgres", "performance", "database"],
    ),
    (
        "Engineering",
        "Incident review: cache stampede",
        """On Tuesday the product API fell over after a cache node restarted. Every request
missed the cache at once and hammered the database, a classic cache stampede.

Fixes shipped:
- Request coalescing so only one request recomputes a missing key.
- Jittered TTLs to avoid synchronised expiry.
- A circuit breaker between the API and the database.

Action item: add a load test that simulates cold caches before each release.""",
        ["incident", "caching", "reliability"],
    ),
    (
        "Reading",
        "Deep Work - key takeaways",
        """Cal Newport argues that the ability to focus without distraction on cognitively
demanding tasks is becoming rare and valuable at the same time.

Practices worth trying:
- Schedule deep work blocks of at least ninety minutes.
- Embrace boredom; do not reach for the phone at every idle moment.
- Quit social media tools that do not provide substantial benefits.
- Drain the shallows: batch email and administrative work.

The most useful idea for me is the shutdown ritual that ends the working day.""",
        ["books", "productivity", "focus"],
    ),
    (
        "Reading",
        "Thinking in systems",
        """A system is a set of elements interconnected so that they produce their own
pattern of behaviour over time. Stocks, flows and feedback loops are the building blocks.

Reinforcing loops amplify change; balancing loops seek a goal. Delays in balancing loops
cause oscillation. Leverage points, from weakest to strongest: constants and parameters,
buffer sizes, information flows, rules, goals, and finally the paradigm the system arises from.""",
        ["books", "systems-thinking"],
    ),
    (
        "Personal",
        "Marathon training plan",
        """Sixteen week plan building from 30 km per week to a peak of 70 km.

Weekly structure: one long run, one tempo run, one interval session and easy runs in between.
Rest is part of the training - schedule a full rest day after the long run.

Nutrition: practise race-day fuelling on long runs, roughly sixty grams of carbohydrate per hour.
Taper for three weeks before race day, cutting volume but keeping intensity.""",
        ["running", "health", "planning"],
    ),
    (
        "Personal",
        "Ideas for the side project",
        """Build a small tool that turns meeting recordings into structured notes with action
items and owners. Start with a command line version that accepts a transcript file.

Potential features: automatic summaries, tagging by project, semantic search across all
meetings, and a weekly digest email. Keep the first version boring and reliable.""",
        ["ideas", "side-project", "ai"],
    ),
    (
        None,
        "Quick note: coffee brewing ratios",
        """Pour-over: 1:16 coffee to water, medium-fine grind, 3 minute total brew.
French press: 1:12, coarse grind, 4 minutes then plunge slowly.
Espresso: 1:2 in about 28 seconds. Adjust grind before adjusting dose.""",
        ["coffee", "recipes"],
    ),
]


async def seed() -> None:
    configure_logging()
    engine = create_engine()
    await init_db(engine)
    factory = create_session_factory(engine)
    async with factory() as db:
        users = UserRepository(db)
        existing = await users.get_by_email(DEMO_EMAIL)
        if existing is not None:
            log.info("demo user already exists (%s); nothing to do", DEMO_EMAIL)
            return
        auth = AuthService(db)
        result = await auth.register(email=DEMO_EMAIL, password=DEMO_PASSWORD, name="Demo User")
        user = await users.get_by_id(result.user.id)
        assert user is not None

        notebook_service = NotebookService(db)
        notebook_ids: dict[str, str] = {}
        for name, description, color in NOTEBOOKS:
            nb = await notebook_service.create(
                NotebookCreate(name=name, description=description, color=color), user
            )
            notebook_ids[name] = nb.id

        note_service = NoteService(db)
        for notebook_name, title, content, tags in NOTES:
            await note_service.create(
                NoteCreate(
                    title=title,
                    content=content.strip(),
                    tags=tags,
                    notebook_id=notebook_ids.get(notebook_name) if notebook_name else None,
                ),
                user,
            )
        await db.commit()
        log.info("seeded %d notebooks and %d notes for %s", len(NOTEBOOKS), len(NOTES), DEMO_EMAIL)
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(seed())
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(130)
