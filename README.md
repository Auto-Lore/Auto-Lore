# Auto-Lore

[![Logic-Service CI](https://github.com/KGvozden/Auto-Lore/actions/workflows/logic-service-ci.yml/badge.svg)](https://github.com/KGvozden/Auto-Lore/actions/workflows/logic-service-ci.yml)
[![Memory-Service CI](https://github.com/KGvozden/Auto-Lore/actions/workflows/memory-service-ci.yml/badge.svg)](https://github.com/KGvozden/Auto-Lore/actions/workflows/memory-service-ci.yml)

A monorepo containing microservices for the Auto-Lore platform.

## Services

| Service | Port | Description |
|---------|------|-------------|
| Memory-Service | 8000 | Handles memory storage and retrieval |
| Logic-Service | 8001 | Handles logic and processing |

## CI/CD Pipelines

Each service has its own GitHub Actions workflow so that changes to one service do not trigger the other's pipeline.

### Memory-Service CI

**Workflow:** `.github/workflows/memory-service-ci.yml`

- **Triggers:** push to `main` or pull request — only when files in `Memory-Service/` change
- **Runs on:** `ubuntu-latest` with Python 3.11
- **Steps:** install dependencies → flake8 lint → pytest

### Logic-Service CI

**Workflow:** `.github/workflows/logic-service-ci.yml`

- **Triggers:** push to `main` or pull request — only when files in `Logic-Service/` or the workflow file itself change
- **Runs on:** `ubuntu-latest` with Python 3.11
- **Steps:** install dependencies → flake8 lint → pytest

Both pipelines follow the same pattern: checkout → setup Python → install from `requirements.txt` → lint → test.
