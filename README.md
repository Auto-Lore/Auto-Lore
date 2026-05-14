# Auto-Lore

[![Memory-Service CI](https://github.com/KGvozden/Auto-Lore/actions/workflows/memory-service-ci.yml/badge.svg)](https://github.com/KGvozden/Auto-Lore/actions/workflows/memory-service-ci.yml)
[![Logic-Service CI](https://github.com/KGvozden/Auto-Lore/actions/workflows/logic-service-ci.yml/badge.svg)](https://github.com/KGvozden/Auto-Lore/actions/workflows/logic-service-ci.yml)
[![Memory-Service Docker](https://github.com/KGvozden/Auto-Lore/actions/workflows/memory-service-docker.yml/badge.svg)](https://github.com/KGvozden/Auto-Lore/actions/workflows/memory-service-docker.yml)

Auto-Lore is a backend platform for AI-driven NPC interactions in a fantasy game. It handles NPC memory (what an NPC remembers about a player across sessions) and generates in-character chat replies via a local LLM. A MAUI game client connects to these services over HTTP.

## Project structure

```
Auto-Lore/
├── Memory-Service/     # NPC memory storage and LLM chat (FastAPI, MongoDB, Ollama)
├── Logic-Service/      # Game logic service (FastAPI — skeleton, extension boundary)
└── .github/workflows/  # CI/CD pipelines (per-service, path-filtered)
```

## Services

| Service | Port | Status | Description |
|---|---|---|---|
| Memory-Service | 8000 | Active | Stores NPC memories in MongoDB; generates chat replies via Ollama |
| Logic-Service | 8001 | Skeleton | Extension boundary for future NPC reasoning and game logic |

## Memory-Service endpoints

- **`/memories`** — CRUD for NPC memory records. Each record stores what an NPC remembers about a player: event type, description, tags, and timestamp.
- **`/chat`** — Accepts a conversation transcript, injects relevant past memories into the system prompt, and returns an in-character NPC reply from a local Ollama model.

NPC personas are defined in `Memory-Service/app/routers/chat.py`. The default model is `llama3.2:3b` and can be overridden with the `OLLAMA_MODEL` environment variable.

## Running locally

**Prerequisites:** Python 3.11+, MongoDB on `localhost:27017`, Ollama running with your chosen model pulled.

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

| Variable | Default | Description |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | `autolore` | MongoDB database name |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model for chat generation |

## Running tests

```bash
cd Memory-Service
python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-fail-under=80

cd Logic-Service
python -m pytest tests/ -v
```

## Docker

Memory-Service is containerised and published to GitHub Container Registry on every merge to `main`.

```bash
# Pull the latest image
docker pull ghcr.io/kgvozden/auto-lore-memory-service:latest

# Run with local MongoDB and Ollama
docker run -p 8000:8000 \
  -e MONGO_URI=mongodb://host.docker.internal:27017 \
  -e OLLAMA_MODEL=llama3.2:3b \
  ghcr.io/kgvozden/auto-lore-memory-service:latest
```

Images are tagged with `latest` (most recent main build) and `sha-<commit>` for full traceability. Pull requests build the image without pushing to validate the Dockerfile.

## CI/CD pipelines

Each workflow is path-filtered — it only runs when files in that service change.

| Workflow | Trigger | Steps |
|---|---|---|
| Memory-Service CI | push/PR → `Memory-Service/` | install → pip-audit → flake8 → pytest + 80% coverage |
| Logic-Service CI | push/PR → `Logic-Service/` | install → flake8 → pytest |
| Memory-Service Docker | push/PR → `Memory-Service/` | build image (PR) / build + push to GHCR (main) |
| Multi-Environment Delivery | manual (`workflow_dispatch`) | deploy-development → deploy-staging → deploy-production |
| DORA Metrics | Monday 09:00 UTC + manual | lead-time-for-changes report across CI workflows |
