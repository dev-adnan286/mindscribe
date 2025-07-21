# MindScribe

AI-powered knowledge notes. Write Markdown notes, group them into notebooks, and let the
assistant summarise them, suggest tags, search by meaning and answer questions with
citations back to your own notes.

Everything works **offline out of the box**: the default `mock` AI provider and the
deterministic `hashing` embedder need no API keys. Point `AI_PROVIDER` at `anthropic`
(model `claude-sonnet-5`) or `openai` when you want real LLM output.

| Layer    | Stack                                                                  |
| -------- | ---------------------------------------------------------------------- |
| Backend  | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, PyJWT, bcrypt   |
| Database | SQLite (`aiosqlite`) for dev/tests, PostgreSQL 16 + pgvector for prod   |
| AI       | Pluggable providers (mock / Anthropic / OpenAI), pluggable embedders    |
| Frontend | Next.js 15 (App Router), React 19, TypeScript strict, Tailwind CSS      |
| State    | TanStack Query (server state), Zustand (auth), Zod (forms)             |
| Tests    | pytest + httpx (backend), Vitest + Testing Library (frontend)           |

## Contents

- [Architecture](#architecture)
- [Features](#features)
- [User interface](#user-interface)
- [Getting started (local)](#getting-started-local)
- [Docker Compose](#docker-compose)
- [Environment variables](#environment-variables)
- [Authentication model](#authentication-model)
- [API reference](#api-reference)
- [Testing and quality](#testing-and-quality)
- [Project structure](#project-structure)

## Architecture

```mermaid
flowchart LR
    subgraph Browser
        UI[Next.js App Router pages]
        RQ[TanStack Query cache]
        Store[Zustand auth store<br/>access token in memory]
    end

    subgraph NextServer[Next.js server]
        MW[middleware.ts<br/>route guard]
        RH[/api/auth/* route handlers<br/>httpOnly refresh cookie/]
    end

    subgraph API[FastAPI backend]
        R[Routers /api/v1]
        S[Services<br/>auth, notes, search, ai]
        Repo[Repositories<br/>SQLAlchemy async]
        Prov[AI provider<br/>mock / anthropic / openai]
        Emb[Embedder<br/>hashing / openai]
    end

    subgraph DB[Database]
        PG[(PostgreSQL 16<br/>+ pgvector)]
        SQ[(SQLite<br/>dev and tests)]
    end

    UI --> RQ --> |Bearer access token| R
    UI --> Store
    UI --> MW
    UI --> |login / refresh / logout| RH --> R
    R --> S --> Repo --> PG
    Repo -.-> SQ
    S --> Prov
    S --> Emb
```

Request flow for a note update: the page debounces edits, `PATCH /notes/{id}` runs
through `NoteService.update`, which bumps the version, writes a `NoteVersion` snapshot,
re-embeds the note, and syncs the `tags` table. Semantic search embeds the query and
ranks notes with pgvector's `<=>` cosine operator on PostgreSQL, or with a numpy cosine
similarity over the stored JSON vectors on SQLite.

## Features

- **Accounts**: register / login with bcrypt-hashed passwords, JWT access tokens (30 min)
  and rotating refresh tokens (14 days) with reuse detection that revokes the whole family.
- **Notebooks**: colour-coded containers; deleting a notebook keeps its notes.
- **Notes**: Markdown content, autosave, soft delete, pagination, filter by notebook / tag /
  keyword, sortable, full version history with one-click restore.
- **Tags**: normalised (`Web Dev` -> `web-dev`), per-user tag table with usage counts.
- **AI summaries and tag suggestions**: apply directly to the note or preview first.
- **Search**: keyword (`LIKE` on SQLite, `tsvector` on PostgreSQL), semantic (pgvector or
  numpy fallback), and hybrid modes with normalised scores.
- **Chat with your notes**: retrieval-augmented answers with numbered citations; sessions
  and messages are persisted; scope a conversation to one notebook.
- **API hygiene**: RFC 7807 `application/problem+json` errors, request IDs, timing headers,
  in-memory rate limiting on auth and AI routes, ownership checks on every resource.
- **Dark mode**, responsive layout, keyboard-friendly forms, toast notifications.

## User interface

- `/` - marketing landing page with feature grid and a three-step "how it works".
- `/login`, `/register` - centred auth cards with inline Zod validation and server error
  mapping (for example duplicate email -> 409 shown under the field).
- `/app` - dashboard: greeting, five stat tiles (notes, notebooks, tags, words, chats),
  recent notes grid, notebook shortcuts.
- `/app/notes` - card grid with a debounced search bar, sort selector, active-filter chips,
  pagination; the left sidebar lists notebooks (with counts) and a tag cloud, and can
  create notebooks through a modal with a colour picker.
- `/app/notes/new` - editor with Write / Split / Preview modes, tag input with AI
  suggestions, notebook selector.
- `/app/notes/[id]` - the same editor with autosave (1.2 s debounce, status text
  "Saving... / All changes saved"), an AI toolbar (Summarize, Suggest tags, History,
  Delete), an AI summary panel, and a slide-in version history drawer with restore.
- `/app/search` - keyword / semantic / hybrid toggle, result cards with a relevance bar
  and percentage, engine badge (`like`, `tsvector`, `numpy-cosine`, `pgvector`).
- `/app/chat` - conversation list, notebook scope selector, message bubbles; assistant
  answers are revealed incrementally and end with citation chips linking to the notes.
- `/app/settings` - profile and password form, theme toggle, AI provider status card.

## Getting started (local)

Prerequisites: Python 3.11+, Node 20+ (Node 22/24 tested), npm. No database server is
required - SQLite is the default.

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # optional: defaults work as-is
python -m scripts.seed           # demo@mindscribe.dev / Password123
uvicorn app.main:app --reload    # http://localhost:8000/docs
```

In development the app creates tables on startup. For PostgreSQL use Alembic instead:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mindscribe alembic upgrade head
```

The initial migration enables the `vector` extension and creates an HNSW cosine index
plus a GIN full-text index when the target is PostgreSQL; on SQLite the embedding column
is plain JSON.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local       # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                      # http://localhost:3000
```

### Makefile shortcuts

`make setup`, `make backend-dev`, `make frontend-dev`, `make seed`, `make test`,
`make lint`, `make compose-up`. Run `make help` for the full list.

## Docker Compose

```bash
docker compose up --build
```

Starts three services: `db` (`pgvector/pgvector:pg16`), `backend` (runs
`alembic upgrade head` then uvicorn on :8000) and `frontend` (standalone Next.js build on
:3000). The frontend's route handlers talk to the API over the compose network via
`API_INTERNAL_URL=http://backend:8000`, while the browser uses
`NEXT_PUBLIC_API_URL=http://localhost:8000`. Pass `AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=...` (or the OpenAI equivalents) as environment variables to enable a
real provider.

## Environment variables

### Backend (`backend/.env`)

| Variable                       | Default                                    | Description                                                   |
| ------------------------------ | ------------------------------------------ | ------------------------------------------------------------- |
| `ENVIRONMENT`                  | `development`                              | `development`, `test` or `production`                         |
| `DATABASE_URL`                 | `sqlite+aiosqlite:///./mindscribe.db`      | SQLAlchemy async URL; use `postgresql+asyncpg://...` for prod   |
| `SECRET_KEY`                   | insecure placeholder                       | JWT signing key - change it in production                     |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | `30`                                       | Access token lifetime                                         |
| `REFRESH_TOKEN_EXPIRE_DAYS`    | `14`                                       | Refresh token lifetime                                        |
| `BCRYPT_ROUNDS`                | `12`                                       | Password hashing cost                                         |
| `CORS_ORIGINS`                 | `http://localhost:3000`                    | Comma-separated allowed origins                               |
| `RATE_LIMIT_ENABLED`           | `true`                                     | Toggle the in-memory limiter                                  |
| `RATE_LIMIT_REQUESTS`          | `120`                                      | Requests per window for AI routes                             |
| `AUTH_RATE_LIMIT_REQUESTS`     | `20`                                       | Requests per window for auth routes                           |
| `RATE_LIMIT_WINDOW_SECONDS`    | `60`                                       | Sliding window length                                         |
| `AI_PROVIDER`                  | `mock`                                     | `mock`, `anthropic` or `openai`                               |
| `EMBEDDING_PROVIDER`           | `hashing`                                  | `hashing` (offline) or `openai`                               |
| `ANTHROPIC_API_KEY`            | -                                          | Required when `AI_PROVIDER=anthropic`                         |
| `ANTHROPIC_MODEL`              | `claude-sonnet-5`                          | Claude model id                                               |
| `OPENAI_API_KEY`               | -                                          | Required for the OpenAI provider or embedder                  |
| `OPENAI_MODEL`                 | `gpt-4o-mini`                              | OpenAI chat model                                             |
| `OPENAI_EMBEDDING_MODEL`       | `text-embedding-3-small`                   | OpenAI embedding model (requested at 256 dimensions)          |
| `CHAT_TOP_K`                   | `5`                                        | Default number of notes retrieved for chat                    |
| `LOG_LEVEL`                    | `INFO`                                     | Python logging level                                          |

Optional SDKs are installed separately: `pip install -e ".[anthropic]"` or `".[openai]"`.
They are imported lazily, so the default install has no dependency on either.

### Frontend (`frontend/.env.local`)

| Variable              | Default                 | Description                                                     |
| --------------------- | ----------------------- | --------------------------------------------------------------- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL used by the browser                                 |
| `API_INTERNAL_URL`    | (falls back to public)  | Backend URL used by the Next.js server (route handlers)         |

## Authentication model

- The backend issues an **access token** (JWT, `type: access`, 30 min) and a **refresh
  token** (JWT, `type: refresh`, 14 days). Refresh tokens are stored hashed with their
  `jti`; every refresh rotates the token and marks the old one as replaced. Presenting a
  rotated token again is treated as theft and revokes every token for that user.
- The browser never stores tokens. The Next.js route handlers under `/api/auth/*` proxy
  login / register / refresh / logout to the API and keep the refresh token in an
  **httpOnly, SameSite=Lax cookie** (`ms_refresh`, `Secure` in production). Only the
  access token is returned to the client, which keeps it in memory (Zustand store).
- The API client attaches `Authorization: Bearer <access>` to requests against
  `NEXT_PUBLIC_API_URL`. On a `401` it calls `POST /api/auth/refresh` once (concurrent
  failures share one refresh), swaps the in-memory token and retries the request.
- `middleware.ts` redirects `/app/*` to `/login?next=...` when the cookie is absent and
  bounces authenticated users away from `/login` and `/register`. The `/app` layout
  re-checks on the client after bootstrapping the session.

## API reference

Base path: `/api/v1`. Interactive docs at `/docs` (Swagger) and `/redoc`. All errors use
`application/problem+json` with `type`, `title`, `status`, `detail`, `instance`,
`request_id` and, for validation failures, an `errors` array.

| Method | Path                                      | Auth | Description                                                      |
| ------ | ----------------------------------------- | ---- | ---------------------------------------------------------------- |
| GET    | `/health`                                 | no   | Status, version, database and AI provider                        |
| POST   | `/auth/register`                          | no   | Create account -> `201` with tokens and user                     |
| POST   | `/auth/login`                             | no   | Exchange credentials for tokens                                  |
| POST   | `/auth/refresh`                           | no   | Rotate refresh token -> new token pair                           |
| POST   | `/auth/logout`                            | no   | Revoke a refresh token -> `204`                                  |
| GET    | `/auth/me`                                | yes  | Current profile                                                  |
| PATCH  | `/auth/me`                                | yes  | Update name and/or password (`current_password`, `new_password`) |
| GET    | `/auth/me/stats`                          | yes  | Counts of notes, notebooks, tags, chats, words                   |
| GET    | `/notebooks`                              | yes  | List notebooks with `note_count`                                 |
| POST   | `/notebooks`                              | yes  | Create (`name`, `description`, `color`) -> `201`                 |
| GET    | `/notebooks/{id}`                         | yes  | Get one                                                          |
| PATCH  | `/notebooks/{id}`                         | yes  | Update                                                           |
| DELETE | `/notebooks/{id}`                         | yes  | Delete; notes are detached -> `204`                              |
| GET    | `/notes`                                  | yes  | Paginated list: `page`, `page_size`, `notebook_id`, `tag`, `q`, `sort` |
| GET    | `/notes/recent?limit=6`                   | yes  | Most recently updated notes                                      |
| POST   | `/notes`                                  | yes  | Create (`title`, `content`, `tags`, `notebook_id`) -> `201`      |
| GET    | `/notes/{id}`                             | yes  | Full note incl. `summary`, `version`, `has_embedding`            |
| PATCH  | `/notes/{id}`                             | yes  | Partial update; content/title/tag changes create a new version   |
| DELETE | `/notes/{id}`                             | yes  | Soft delete -> `204`                                             |
| GET    | `/notes/{id}/versions`                    | yes  | Version history (newest first)                                   |
| POST   | `/notes/{id}/versions/{version}/restore`  | yes  | Restore a snapshot as a new version                              |
| GET    | `/tags`                                   | yes  | Tags with note counts                                            |
| GET    | `/search?q=&mode=&limit=`                 | yes  | `mode` = `keyword`, `semantic` or `hybrid`; hits carry a 0-1 score |
| GET    | `/ai/status`                              | yes  | Active provider, model, embedder                                 |
| POST   | `/ai/summarize`                           | yes  | `{note_id | content, apply?, max_sentences?}`                    |
| POST   | `/ai/tags`                                | yes  | `{note_id | content, apply?, max_tags?}`                         |
| POST   | `/ai/ask`                                 | yes  | `{question, session_id?, notebook_id?, top_k?}` -> answer + citations |
| GET    | `/ai/sessions`                            | yes  | Chat sessions with message counts                                |
| GET    | `/ai/sessions/{id}/messages`              | yes  | Messages in a session                                            |
| DELETE | `/ai/sessions/{id}`                       | yes  | Delete a session -> `204`                                        |

Example:

```bash
curl -s -X POST localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@mindscribe.dev","password":"Password123"}' | jq -r .access_token
```

```bash
curl -s "localhost:8000/api/v1/search?q=cache%20stampede&mode=semantic" \
  -H "Authorization: Bearer $TOKEN" | jq '.hits[] | {title, score}'
```

## Testing and quality

Backend (SQLite, isolated database per test, mock AI provider):

```bash
cd backend
pytest -q                 # 41 tests: auth flow, notebooks, notes, versions, search, AI, health
ruff check app tests scripts alembic && ruff format --check app tests scripts alembic
mypy app
```

Frontend:

```bash
cd frontend
npm run lint              # ESLint (next/core-web-vitals + next/typescript)
npx tsc --noEmit          # strict TypeScript incl. noUncheckedIndexedAccess
npm test                  # Vitest + Testing Library: components, API client (401 -> refresh), utils
npm run build             # production build (standalone output)
```

CI (`.github/workflows/ci.yml`) runs the backend suite on Python 3.11 and 3.12 and the
frontend lint / typecheck / test / build on Node 22.

## Project structure

```
mindscribe/
├── backend/
│   ├── alembic/                  # env.py + versions/0001_initial_schema.py
│   ├── app/
│   │   ├── ai/                   # providers (base, mock, anthropic, openai), embeddings, factory, text utils
│   │   ├── api/v1/routers/       # auth, notebooks, notes, tags, search, ai, health
│   │   ├── core/                 # config, security, deps, exceptions (RFC 7807), rate_limit, logging
│   │   ├── db/                   # engine/session, Base, models, EmbeddingType (pgvector / JSON)
│   │   ├── repositories/         # query layer per aggregate
│   │   ├── schemas/              # pydantic v2 request/response models
│   │   ├── services/             # auth, notebooks, notes, search, ai
│   │   └── main.py               # app factory, middleware, lifespan
│   ├── scripts/seed.py           # demo user + sample notes
│   ├── tests/                    # pytest suite (SQLite)
│   ├── Dockerfile, pyproject.toml, alembic.ini, .env.example
├── frontend/
│   ├── src/app/                  # App Router: landing, (auth)/login+register, app/* pages, api/auth/* handlers
│   ├── src/components/           # Navbar, Sidebar, NoteCard, NoteEditor, TagInput, SearchBar, Chat*, Modal, Toast, ...
│   ├── src/lib/api/              # typed client with auto-refresh, endpoints, types
│   ├── src/lib/auth/             # zustand store, provider, hooks
│   ├── src/lib/server/           # cookie helpers for route handlers
│   ├── src/lib/                  # schemas (zod), utils, hooks
│   ├── src/middleware.ts         # edge route guard
│   ├── Dockerfile, package.json, tsconfig.json, vitest.config.ts, .env.example
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Makefile
├── LICENSE (MIT)
└── README.md
```

## License

MIT - see [LICENSE](LICENSE).
