import logging
import os
from contextlib import asynccontextmanager

import ollama
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, memories

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("memory_service")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    # Warm up the model on startup so the first /chat request isn't slow
    try:
        available = {m.model for m in ollama.list().models}
        if model not in available:
            raise RuntimeError(
                f"Ollama model '{model}' is not pulled. "
                f"Run: ollama pull {model}"
            )
        logger.info("Warming Ollama model '%s' …", model)
        ollama.chat(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            options={"num_predict": 1},
        )
        logger.info("Ollama warm-up complete.")
    except RuntimeError:
        raise
    except Exception as exc:
        logger.warning(
            "Ollama warm-up failed (%s: %s) — first /chat may be slow.",
            type(exc).__name__, exc,
        )

    yield


app = FastAPI(title="Memory Service", lifespan=lifespan)

# Allow any localhost origin so the dev client and Swagger UI can connect
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memories.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "memory-service"}
