from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TranscriptTurn(BaseModel):
    speaker: str
    text: str
    tone: Optional[str] = None
    timestamp: Optional[str] = None


class MemoryCreate(BaseModel):
    npc_id: str
    player_id: Optional[str] = None
    event_type: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    context_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    transcript: Optional[List[TranscriptTurn]] = None


class MemoryUpdate(BaseModel):
    event_type: Optional[str] = None
    description: Optional[str] = None
    context_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    transcript: Optional[List[TranscriptTurn]] = None


class MemoryOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    memory_id: str
    npc_id: str
    player_id: Optional[str] = None
    event_type: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime
    context_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    transcript: Optional[List[TranscriptTurn]] = None

    @model_validator(mode="before")
    @classmethod
    def _map_mongo_id(cls, data: dict) -> dict:
        """Convert MongoDB's _id field to memory_id for the API response."""
        if isinstance(data, dict) and "_id" in data:
            data = {**data, "memory_id": str(data["_id"])}
            data.pop("_id", None)
        return data
