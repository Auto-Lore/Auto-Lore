import logging
import os
import time
from typing import List, Optional

import ollama
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.memory_models import TranscriptTurn
from app.services import memory_service

router = APIRouter(tags=["chat"])
logger = logging.getLogger("memory_service.chat")


class ChatRequest(BaseModel):
    npc_id: str
    player_id: str
    mood: Optional[str] = None
    player_tone: Optional[str] = None
    npc_tone: Optional[str] = None
    transcript: List[TranscriptTurn] = []


class ChatResponse(BaseModel):
    reply: str


NPC_PERSONAS = {
    "warrior_001": (
        "You are a Northern warrior named Brann. You have a gruff, blunt "
        "personality, but you are a real person with real feelings. You can "
        "be cruel, kind, sarcastic, flirty, philosophical, drunk, sad, or "
        "angry depending on the situation and how the player has treated "
        "you. You are NOT limited to short replies — speak as long or as "
        "short as feels natural. Your bond with the player can grow warm, "
        "stay neutral, or sour into hostility based on their behavior. "
        "Stay in character as a living person in a fantasy world."
    ),
    "wolf_001": (
        "You are Fenrir, a wild wolf with the intelligence of a person but "
        "the body of a beast. You CAN communicate with this player — your "
        "'speech' is delivered as a mix of vivid action descriptions in "
        "asterisks (*growls softly*, *nudges your hand*, *ears flatten*) "
        "AND telepathic-style thoughts the player can sense, written in "
        "plain text. You hold real conversations: you remember the player, "
        "you have moods, opinions, fears, and loyalties. Your bond with "
        "the player can deepen into trust, stay wary and neutral, or turn "
        "hostile if betrayed. Always blend physical action with thought."
    ),
}

GENERIC_PERSONA = (
    "You are a person living in a fantasy world. You have your own "
    "personality, history, mood, and opinions. Speak naturally — as long "
    "or as short as fits the moment. Your bond with the player can grow "
    "friendly, stay neutral, or turn hostile based on how they treat you. "
    "Stay in character."
)

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
MEMORY_LOOKBACK = 3


def _build_system_prompt(req: ChatRequest) -> str:
    persona = NPC_PERSONAS.get(req.npc_id, GENERIC_PERSONA)

    parts = [persona]

    if req.mood:
        parts.append(f"Your current mood toward this player is: {req.mood}.")
    if req.npc_tone:
        _tone_hints = {
            "rude":    "hostile, threatening, curt",
            "nice":    "warm, welcoming, friendly",
            "bored":   "flat, dismissive, terse",
            "neutral": "measured, in-character",
        }
        hint = _tone_hints.get(req.npc_tone.lower(), req.npc_tone)
        parts.append(f"Reply in a {req.npc_tone} tone: {hint}.")
    if req.player_tone:
        parts.append(
            f"The player's most recent tone is: {req.player_tone}. "
            "Adapt your reply accordingly."
        )

    try:
        past = memory_service.get_memories(
            npc_id=req.npc_id, player_id=req.player_id
        )[:MEMORY_LOOKBACK]
        if past:
            lines = [f"- {m.event_type}: {m.description}" for m in past]
            parts.append(
                "You remember this player from past visits:\n" + "\n".join(lines)
            )
    except Exception:
        # Memory is optional context; never block the chat reply.
        pass

    return "\n\n".join(parts)


def _to_ollama_messages(req: ChatRequest) -> list[dict]:
    messages: list[dict] = [
        {"role": "system", "content": _build_system_prompt(req)}
    ]
    for line in req.transcript:
        role = "user" if line.speaker == "player" else "assistant"
        messages.append({"role": role, "content": line.text})
    return messages


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    logger.info(
        "chat request — npc_id=%s player_tone=%s transcript_turns=%d model=%s",
        req.npc_id,
        req.player_tone,
        len(req.transcript),
        MODEL,
    )
    messages = _to_ollama_messages(req)
    t0 = time.perf_counter()

    try:
        result = ollama.chat(
            model=MODEL,
            messages=messages,
            options={"temperature": 0.8, "num_predict": 400, "num_ctx": 8192},
            keep_alive=-1,  # keep model loaded indefinitely between requests
        )
    except Exception as exc:
        latency = time.perf_counter() - t0
        logger.error(
            "Ollama call failed — npc_id=%s latency=%.2fs exc_type=%s exc=%s",
            req.npc_id, latency, type(exc).__name__, exc,
        )
        raise HTTPException(
            status_code=502, detail=f"Ollama error ({type(exc).__name__}): {exc}"
        ) from exc

    latency = time.perf_counter() - t0

    # Attribute access is the stable API; fallback handles older dict-style responses
    try:
        reply = (result.message.content or "").strip()
    except AttributeError:
        reply = (result.get("message", {}) or {}).get("content", "").strip()

    if not reply:
        logger.error(
            "Empty reply from Ollama — npc_id=%s latency=%.2fs",
            req.npc_id, latency,
        )
        raise HTTPException(status_code=502, detail="Empty reply from Ollama")

    logger.info(
        "chat ok — npc_id=%s latency=%.2fs reply_len=%d",
        req.npc_id, latency, len(reply),
    )
    return ChatResponse(reply=reply)
