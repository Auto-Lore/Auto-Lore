# Logic-Service

A lightweight FastAPI microservice running on port **8001**.

Currently exposes a single health monitoring endpoint. It exists as the extension boundary for future NPC reasoning and game business logic, with its structure already in place across `app/routers/`, `app/services/`, `app/models/`, and `app/db/`.

Has independent CI validation in the monorepo — changes to this service trigger its own pipeline without affecting Memory-Service.

## Running locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## Running tests

```bash
pytest tests/ -v
```
