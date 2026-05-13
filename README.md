# Auto-Lore

[![Logic-Service CI](https://github.com/KGvozden/Auto-Lore/actions/workflows/logic-service-ci.yml/badge.svg)](https://github.com/KGvozden/Auto-Lore/actions/workflows/logic-service-ci.yml)
[![Memory-Service CI](https://github.com/KGvozden/Auto-Lore/actions/workflows/memory-service-ci.yml/badge.svg)](https://github.com/KGvozden/Auto-Lore/actions/workflows/memory-service-ci.yml)

Auto-Lore is a backend platform for AI-driven NPC interactions in a fantasy game. It handles NPC memory (what an NPC remembers about a player across sessions) and chat (generating in-character replies via a local LLM). A MAUI game client connects to these services over HTTP.

## Project structure

```
Auto-Lore/
├── Memory-Service/     # NPC memory storage and LLM chat (FastAPI, MongoDB, Ollama)
├── Logic-Service/      # Game logic service (FastAPI — skeleton, in progress)
└── .github/workflows/  # CI pipelines (one per service)
```

## Services

| Service | Port | Status | Description |
|---------|------|--------|-------------|
| Memory-Service | 8000 | Active | Stores NPC memories in MongoDB; generates chat replies via Ollama |
| Logic-Service  | 8001 | Skeleton | Placeholder for future game logic endpoints |

## Memory-Service

Provides two groups of endpoints:

- **`/memories`** — CRUD for NPC memory records. Each record stores what an NPC remembers about a player: event type, description, tags, and the conversation transcript.
- **`/chat`** — Sends a conversation transcript to a local Ollama model and returns an in-character NPC reply. Memories from past sessions are injected into the system prompt automatically.

NPC personas are defined in `Memory-Service/app/routers/chat.py`. The default model is `llama3.2:3b` and can be overridden with the `OLLAMA_MODEL` environment variable.

## Running locally

**Prerequisites:** Python 3.11+, MongoDB running on `localhost:27017`, Ollama running with your chosen model pulled.

```bash
# Memory-Service
cd Memory-Service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Logic-Service (separate terminal)
cd Logic-Service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Environment variables (optional — defaults work for local dev):

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | `autolore` | MongoDB database name |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model to use for chat |

## Running tests

```bash
# From each service directory
cd Memory-Service
pytest tests/ -v --cov=. --cov-report=term-missing

cd Logic-Service
pytest tests/ -v
```

## CI/CD

Each service has its own GitHub Actions workflow that triggers only when files in that service change. Both pipelines run on Python 3.11 and follow the same steps: install dependencies → flake8 lint → pytest. Memory-Service additionally enforces 80% test coverage.

| Workflow | File |
|----------|------|
| Logic-Service CI | `.github/workflows/logic-service-ci.yml` |
| Memory-Service CI | `.github/workflows/memory-service-ci.yml` |
