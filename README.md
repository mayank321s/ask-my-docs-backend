# Ask My Docs — Backend

A Retrieval-Augmented Generation (RAG) API that turns your documents and GitHub code into a searchable, conversational knowledge base.

Upload PDFs, Word files, or plain text, or sync a GitHub repository and its merged pull requests. Ask My Docs chunks the content, embeds it locally with Ollama, stores the vectors in Qdrant, and answers natural-language questions with an OpenAI model grounded in the retrieved context. It supports multi-turn chat, persisted history, and token-by-token streaming.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Core Concepts](#core-concepts)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage Walkthrough](#usage-walkthrough)
- [API Reference](#api-reference)
- [Database Migrations](#database-migrations)
- [Project Structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

- **Document ingestion**: upload `.pdf`, `.docx`, and plain-text files. Text is extracted, split into overlapping chunks, embedded, and indexed in a background task.
- **GitHub ingestion**:
  - Sync a whole repository branch (downloaded as a zipball, every readable file indexed).
  - Index a single pull request, storing **before and after** versions of every changed file along with PR metadata (title, author, description, merge date).
  - Bulk-index **all merged PRs** in a repository.
  - Use a personal GitHub token per user, list a user's repositories and branches, and track sync status.
- **Semantic search** over Qdrant, scoped to one category or across every category in a project.
- **Conversational answers** from OpenAI, with:
  - Session-based memory (multi-turn follow-ups).
  - Streaming responses (`text/event-stream`) through an OpenAI-compatible gateway (Vercel AI Gateway by default).
  - Chat history saved to PostgreSQL and listed with pagination.
- **Multi-tenant by design**: JWT authentication, projects owned by users, and categories implemented as Qdrant tenant-indexed namespaces.
- **Async throughout**: FastAPI, Tortoise ORM with asyncpg, and background tasks for long-running ingestion.

---

## Architecture

```
                 ┌──────────────────────────────────────────────┐
  Client ──JWT──▶│                 FastAPI app                  │
                 │  /v2/auth  /v2/projects  /v2/documents       │
                 │  /v2/github  /v2/chat                        │
                 └───────┬───────────────┬──────────────┬───────┘
                         │               │              │
                 ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼────────────┐
                 │  PostgreSQL  │ │   Qdrant    │ │  OpenAI / AI     │
                 │ (Tortoise)   │ │  vectors    │ │  Gateway (LLM)   │
                 │ users, chats │ │ 1 collection│ └──────────────────┘
                 │ projects ... │ │ per project │
                 └──────────────┘ └──────▲──────┘
                                         │ embeddings
                                  ┌──────┴──────┐        ┌──────────┐
                                  │   Ollama    │        │  GitHub  │
                                  │ nomic-embed │        │ REST API │
                                  └─────────────┘        └──────────┘
```

**Ingestion flow:** extract text → `RecursiveCharacterTextSplitter` (300 chars, 30 overlap) → `nomic-embed-text` embeddings (768-dim) via Ollama → upsert into the project's Qdrant collection, tagged with the category's `namespace` → record the document and chunk IDs in PostgreSQL.

**Query flow:** embed the question → filtered vector search in Qdrant (one namespace or all of them) → build a prompt from the retrieved chunks, their metadata, and recent chat history → OpenAI completion (blocking or streamed) → save the turn to the `chats` table.

---

## Tech Stack

| Layer            | Technology                                                    |
| ---------------- | ------------------------------------------------------------- |
| API framework    | FastAPI, Starlette, Pydantic v2                               |
| Database / ORM   | PostgreSQL, Tortoise ORM, asyncpg, Aerich (migrations)        |
| Vector store     | Qdrant (`qdrant-client`), cosine distance, 768-dim vectors    |
| Embeddings       | Ollama, `nomic-embed-text`                                    |
| LLM              | OpenAI via `langchain-openai` / `openai` SDK (gateway-capable) |
| Orchestration    | LangChain (text splitting, prompt templates, message history) |
| File parsing     | PyMuPDF (`fitz`), `python-docx`                               |
| Auth             | PyJWT (HS256), bcrypt                                         |
| HTTP clients     | `httpx`, `requests` (GitHub API)                              |

> Legacy integrations (Pinecone, Hugging Face / Together, Ollama chat models) remain in `app/core` and the `v1` API. The `v2` API is the current, supported surface.

---

## Core Concepts

| Concept      | What it is                                                                                     | Storage                                       |
| ------------ | ---------------------------------------------------------------------------------------------- | --------------------------------------------- |
| **User**     | An account that registers and logs in, identified by a JWT. Role is `user` by default.         | `users`                                       |
| **Project**  | A top-level knowledge base owned by a user. Each project gets its **own Qdrant collection**, named after the project in lowercase with spaces replaced by hyphens. | `projects`, `vector_indexes`                   |
| **Category** | A logical partition inside a project, such as "Specs", "Backend repo", or "HR policies". Implemented as a `namespace` payload field on Qdrant points (tenant-indexed). | `vector_namespaces`                            |
| **Document** | A file or code artifact indexed into a category. Its chunk IDs are tracked for cleanup.         | `documents`, `vector_chunks`                  |
| **Chat**     | A session of user/assistant turns tied to a project, and optionally a category.                | `chats`                                       |
| **GitHub**   | Per-user tokens, synced repos, branches, and pull requests, each with an ingestion `status`.   | `github_token`, `github_repo`, `github_branch`, `github_pull_request` |

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **PostgreSQL 13+**
- **Qdrant** (local Docker or Qdrant Cloud)
- **Ollama** running locally, with the `nomic-embed-text` model pulled
- An **OpenAI API key** and/or an **OpenAI-compatible gateway key** (Vercel AI Gateway by default) for streaming
- *(Optional)* A **GitHub personal access token** for repository and PR ingestion

### 1. Clone the repository

```bash
git clone https://github.com/mayank321s/ask-my-docs-backend.git
cd ask-my-docs-backend
git checkout develop
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install ollama python-dotenv httpx requests
```

> The second line installs packages the code imports that `requirements.txt` doesn't list yet.

### 4. Start the backing services

**PostgreSQL:** use an existing instance, or run:

```bash
docker run -d --name askmydocs-postgres \
  -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16
```

**Qdrant:**

```bash
docker run -d --name askmydocs-qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v "$(pwd)/qdrant_data:/qdrant/storage" \
  qdrant/qdrant:v1.13.4
```

**Ollama:** install it from [ollama.com](https://ollama.com), then:

```bash
ollama pull nomic-embed-text
ollama serve        # skip if the Ollama desktop app is already running
```

### 5. Configure the environment

```bash
cp .env.example .env
```

Fill in the values described in [Configuration](#configuration).

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

On startup, Tortoise creates any missing tables (`generate_schemas=True`). For controlled schema changes, use [Aerich migrations](#database-migrations).

- API base: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## Configuration

All configuration comes from environment variables. `app/config/db.py` loads them from `.env` at startup.

| Variable               | Required | Description                                                                   |
| ---------------------- | :------: | ----------------------------------------------------------------------------- |
| `POSTGRES_USER`        |    ✅    | PostgreSQL user                                                               |
| `POSTGRES_PASSWORD`    |    ✅    | PostgreSQL password                                                           |
| `POSTGRES_DB`          |    ✅    | Database name                                                                 |
| `POSTGRES_HOST`        |    ✅    | Database host, such as `localhost`                                            |
| `POSTGRES_PORT`        |    ✅    | Database port, such as `5432`                                                 |
| `JWT_SECRET_KEY`       |    ✅    | Secret used to sign HS256 access tokens. Use a long random string.            |
| `JWT_EXPIRATION_HOURS` |          | Token lifetime in hours. Defaults to `24`.                                    |
| `QDRANT_URL`           |    ✅    | Qdrant endpoint, such as `http://localhost:6333`                              |
| `QDRANT_API_KEY`       |          | Qdrant API key. Required for Qdrant Cloud or secured instances.               |
| `OPENAI_MODEL`         |    ✅    | Chat model name, such as `gpt-4o`. For the gateway, use the gateway's model ID, such as `openai/gpt-4o`. |
| `OPENAI_API_KEY`       |    ✅    | Used by the non-streaming `/v2/chat/` endpoint (LangChain `ChatOpenAI`).      |
| `AI_GATEWAY_API_KEY`   |    ✅*   | API key for the OpenAI-compatible gateway used by `/v2/chat/stream`.          |
| `OPENAI_BASE_URL`      |          | Gateway base URL for streaming. Defaults to `https://ai-gateway.vercel.sh/v1`. |
| `GITHUB_TOKEN`         |          | Fallback GitHub token for users who haven't stored their own.                 |
| `OLLAMA_HOST`          |          | Ollama server address, if it isn't `http://127.0.0.1:11434`. Read by the `ollama` client. |
| `HF_TOKEN`             |          | Hugging Face token. Legacy v1 LLM path only.                                  |
| `PINECONE_API_KEY`     |          | Pinecone key. Legacy v1 vector path only.                                     |
| `AZURE_API_KEY`        |          | Reserved; not read by the current code.                                       |

\* Required if you use streaming chat.

Example `.env` for local development:

```dotenv
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

JWT_SECRET_KEY=change-me-to-a-long-random-string
JWT_EXPIRATION_HOURS=24

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

OPENAI_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
AI_GATEWAY_API_KEY=...
# OPENAI_BASE_URL=https://ai-gateway.vercel.sh/v1

GITHUB_TOKEN=
```

> Never commit a real `.env`. It is already listed in `.gitignore`.

---

## Usage Walkthrough

The examples below use `curl` against `http://localhost:8000`. Every endpoint except register and login requires the header `Authorization: Bearer <accessToken>`.

### 1. Register and log in

```bash
curl -X POST http://localhost:8000/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{"firstName":"Ada","lastName":"Lovelace","emailAddress":"ada@example.com","password":"s3cret!"}'

curl -X POST http://localhost:8000/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"emailAddress":"ada@example.com","password":"s3cret!"}'
```

The login response contains `accessToken` and `githubToken`, a boolean that says whether the user has stored a GitHub token.

```bash
export TOKEN="<accessToken>"
```

### 2. Create a project and a category

```bash
# Creates the project and its Qdrant collection ("engineering-handbook")
curl -X POST http://localhost:8000/v2/projects/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Engineering Handbook"}'

# List projects to get the project ID
curl "http://localhost:8000/v2/projects/?page=1&limit=10" -H "Authorization: Bearer $TOKEN"

# Create a category inside project 1
curl -X POST http://localhost:8000/v2/projects/1/category \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Architecture"}'

# List categories to get the category ID
curl http://localhost:8000/v2/projects/1/category -H "Authorization: Bearer $TOKEN"
```

### 3. Add content

**Upload a document.** `metadata` must be a JSON string. Its fields are stored on every chunk and passed to the LLM as context.

```bash
curl -X POST http://localhost:8000/v2/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F projectId=1 \
  -F categoryId=1 \
  -F 'metadata={"team":"platform","version":"2.1"}' \
  -F file=@./docs/system-design.pdf
```

**Sync a GitHub repository.** Store a token first if the repository is private.

```bash
curl -X POST "http://localhost:8000/v2/github/store-github-token?githubToken=ghp_xxx" \
  -H "Authorization: Bearer $TOKEN"

# Entire repository (default branch, or the branch in a /tree/<branch> URL)
curl "http://localhost:8000/v2/github/download?repoUrl=https://github.com/org/repo&projectId=1&categoryId=1" \
  -H "Authorization: Bearer $TOKEN"

# A single pull request (before and after content of every changed file)
curl "http://localhost:8000/v2/github/fetch-pr-files?prUrl=https://github.com/org/repo/pull/42&projectId=1&categoryId=1" \
  -H "Authorization: Bearer $TOKEN"

# Every merged pull request in the repository
curl "http://localhost:8000/v2/github/fetch-all-merged-pr?repoUrl=https://github.com/org/repo&projectId=1&categoryId=1" \
  -H "Authorization: Bearer $TOKEN"
```

Ingestion runs in the background, and the endpoints return immediately. To check progress, use `GET /v2/github/get-all-synced-repositories` or `GET /v2/projects/{categoryId}/get-all-synced-data`. Each status is one of `uploading`, `active`, or `failed`.

### 4. Ask questions

**Standard response, with memory:**

```bash
curl -X POST http://localhost:8000/v2/chat/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"projectId":1,"categoryId":1,"query":"How does the auth service issue tokens?"}'
```

```json
{
  "answer": "…",
  "sessionId": "6f1c…",
  "memoryEnabled": true,
  "contextChunksCount": 10
}
```

- Leave out `categoryId` to search across **every category** in the project.
- To ask a follow-up in the same conversation, send the returned `sessionId`. The project and category are then taken from the saved session.
- Add `?use_memory=false` for a one-off answer with no session.

**Streaming response:**

```bash
curl -N -X POST http://localhost:8000/v2/chat/stream \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"projectId":1,"query":"Summarise the last 5 merged PRs"}'
```

- The response is `text/event-stream`. Events are separated by a blank line. Each event is an OpenAI `chat.completion.chunk` JSON object, so read the text from `choices[0].delta.content`. The stream ends with `[DONE]`.
- The session ID comes back in the `X-Session-Id` response header. The full answer is saved to chat history when the stream finishes, including when the client disconnects early.

**Browse history:**

```bash
curl "http://localhost:8000/v2/chat/history?page=1&limit=10" -H "Authorization: Bearer $TOKEN"
curl http://localhost:8000/v2/chat/history/<sessionId> -H "Authorization: Bearer $TOKEN"
```

---

## API Reference

All `v2` routes are prefixed with `/v2`. 🔒 means a Bearer JWT is required. The interactive documentation at `/docs` shows the full request and response schemas.

### Auth

| Method | Path              | Description                          |
| ------ | ----------------- | ------------------------------------ |
| POST   | `/auth/register`  | Create an account                    |
| POST   | `/auth/login`     | Get a JWT access token               |

### Projects & Categories 🔒

| Method | Path                                         | Description                                              |
| ------ | -------------------------------------------- | -------------------------------------------------------- |
| POST   | `/projects/`                                 | Create a project and its Qdrant collection               |
| GET    | `/projects/?page=&limit=`                    | List your projects (paginated)                           |
| DELETE | `/projects/{projectId}`                      | Delete a project and its collection                      |
| POST   | `/projects/{projectId}/category`             | Create a category (namespace)                            |
| GET    | `/projects/{projectId}/category`             | List a project's categories                              |
| DELETE | `/projects/{projectId}/category/{categoryId}`| Delete a category and its vectors                        |
| GET    | `/projects/{categoryId}/get-all-synced-data` | Documents and GitHub items synced into a category        |

### Documents 🔒

| Method | Path                       | Description                                                         |
| ------ | -------------------------- | ------------------------------------------------------------------- |
| POST   | `/documents/upload`        | Multipart upload: `file`, `projectId`, `categoryId`, `metadata` (JSON string) |
| GET    | `/documents/{categoryId}`  | List the documents in a category                                    |
| DELETE | `/documents/{documentId}`  | Delete a document's records                                         |

### GitHub 🔒

| Method | Path                               | Query parameters                         | Description                                    |
| ------ | ---------------------------------- | ---------------------------------------- | ---------------------------------------------- |
| POST   | `/github/store-github-token`       | `githubToken`                            | Save or replace your GitHub PAT                |
| GET    | `/github/get-github-token`         | —                                        | Check whether a token is stored                |
| GET    | `/github/get-all-repositories`     | —                                        | List your GitHub repositories and their branches |
| GET    | `/github/download`                 | `repoUrl`, `projectId`, `categoryId`     | Index a whole repository branch                |
| GET    | `/github/fetch-pr-files`           | `prUrl`, `projectId`, `categoryId`       | Index one pull request                         |
| GET    | `/github/fetch-all-merged-pr`      | `repoUrl`, `projectId`, `categoryId`     | Index every merged pull request                |
| GET    | `/github/get-all-synced-repositories` | `projectId?`, `categoryId?`, `repoName?` | Synced repositories and their status        |

### Chat 🔒

| Method | Path                              | Description                                         |
| ------ | --------------------------------- | --------------------------------------------------- |
| POST   | `/chat/?use_memory=true`          | Search and answer (JSON response)                   |
| POST   | `/chat/stream`                    | Search and answer, streamed (`text/event-stream`)   |
| GET    | `/chat/history?page=&limit=`      | Your saved conversations (paginated)                |
| GET    | `/chat/history/{session_id}`      | One saved conversation                              |
| GET    | `/chat/session/{session_id}/history` | In-memory history for a session                  |
| DELETE | `/chat/session/{session_id}`      | Clear a session's in-memory history                 |
| POST   | `/chat/session/{session_id}/clear`| Same as above, using POST                           |
| GET    | `/chat/health`                    | Chat service health check                           |

**Chat request body** (`SearchAndAnswerRequestDto`):

```json
{
  "query": "string (required)",
  "projectId": 1,
  "categoryId": 1,
  "sessionId": "optional – continue an existing conversation"
}
```

> The un-prefixed `v1` routes (`/projects`, `/documents`, `/chat`, `/github`) are still mounted for backward compatibility but are deprecated. Use `v2` for new work.

---

## Database Migrations

The project uses [Aerich](https://github.com/tortoise/aerich) with Tortoise ORM. The configuration is in `pyproject.toml` under `[tool.aerich]` and in `app/config/aerich.py`.

```bash
aerich init-db                         # first time only
aerich migrate --name "describe_change"
aerich upgrade                         # apply pending migrations
aerich downgrade                       # roll back the last migration
aerich history                         # list applied migrations
```

See [MIGRATION_USAGE.md](MIGRATION_USAGE.md) for a full walkthrough.

---

## Project Structure

```
ask-my-docs-backend/
├── app/
│   ├── main.py                  # FastAPI app, CORS, startup
│   ├── initializer.py           # Registers routers, DB, exception handlers
│   ├── api/
│   │   ├── v1/                  # Legacy endpoints (deprecated)
│   │   └── v2/                  # Current API
│   │       ├── auth/            #   register / login
│   │       ├── projects/        #   projects & categories
│   │       ├── documents/       #   file upload & management
│   │       ├── github/          #   repo / PR ingestion
│   │       └── chat/            #   RAG chat, streaming, history
│   ├── config/                  # DB, Aerich, and OpenAPI settings
│   ├── core/
│   │   ├── chunker/             # LangChain text splitter
│   │   ├── llm/                 # OpenAI, gateway streaming, legacy HF/Ollama
│   │   ├── qdrant/              # Collections, namespaces, upsert, search
│   │   ├── pinecone/            # Legacy vector client
│   │   ├── models/
│   │   │   ├── pydantic/        # Request/response DTOs
│   │   │   └── tortoise/        # ORM models
│   │   ├── repository/          # Data-access layer per model
│   │   ├── routers/             # Router registration and auth dependencies
│   │   └── exceptions/          # ORM exception handlers
│   └── utils/                   # JWT, password hashing, file parsing, pagination
├── migrations/                  # Aerich migration files
├── scripts/                     # Docker helper scripts
├── tests/                       # Pytest suite
├── tdd.md                       # Technical design document
├── MIGRATION_USAGE.md           # Migration guide
├── Dockerfile
├── Makefile
└── requirements.txt
```

**Layering:** each feature is split into a controller (HTTP routing), a service (business logic), and a repository (database access), with Qdrant and LLM clients in `app/core`. A new feature should follow the same three files under `app/api/v2/<feature>/`, and its router should be registered in `app/core/routers/__init__.py`.

---

## Development

```bash
# Format the code
black app/

# Install the pre-commit hooks
pre-commit install

# Run the tests (API_TEST=1 switches the app to in-memory SQLite)
API_TEST=1 python -m pytest --cov=app --verbose tests/
```

### Docker

```bash
docker build -t ask-my-docs-backend .
docker run --env-file .env -p 8000:80 ask-my-docs-backend
```

The image is based on `tiangolo/uvicorn-gunicorn-fastapi`, which serves `app.main:app` on port 80. PostgreSQL, Qdrant, and Ollama must be reachable from inside the container. When they run on the host, set `POSTGRES_HOST`, `QDRANT_URL`, and `OLLAMA_HOST` to `host.docker.internal`.

---

## Troubleshooting

| Symptom                                          | Likely cause and fix                                                                  |
| ------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: ollama` / `dotenv`         | Run `pip install ollama python-dotenv httpx requests`.                                |
| `Connection refused` while embedding             | Ollama isn't running, or `nomic-embed-text` isn't pulled. Run `ollama pull nomic-embed-text`. |
| `Project index not found` when chatting          | The project has no `vector_indexes` row. Recreate the project through the API.       |
| `Namespace not found`                            | The `categoryId` doesn't exist. List categories with `GET /v2/projects/{id}/category`. |
| `401 Invalid token`                              | The token expired or `JWT_SECRET_KEY` changed. Log in again.                          |
| Qdrant dimension mismatch on upsert              | The collection was created with a different embedding size. It must be 768 for `nomic-embed-text`. |
| GitHub `403` / rate limit                        | Store a personal access token with `POST /v2/github/store-github-token`, or set `GITHUB_TOKEN`. |

---

## License

No license has been chosen yet; the [LICENSE](LICENSE) file is currently empty. Until one is added, all rights are reserved by the repository owner.
