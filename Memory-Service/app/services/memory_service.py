import re
from typing import List, Optional

from bson import ObjectId
from bson.errors import InvalidId

from app.db.mongo import memories_collection
from app.models.memory_models import MemoryCreate, MemoryOut, MemoryUpdate


def _to_object_id(memory_id: str) -> Optional[ObjectId]:
    try:
        return ObjectId(memory_id)
    except (InvalidId, TypeError):
        return None


def create_memory(data: MemoryCreate) -> MemoryOut:
    document = data.model_dump()
    result = memories_collection.insert_one(document)
    doc = memories_collection.find_one({"_id": result.inserted_id})
    return MemoryOut.model_validate(doc)


def get_memories(
    npc_id: Optional[str] = None,
    player_id: Optional[str] = None,
    event_type: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[MemoryOut]:
    query = {}
    if npc_id:
        query["npc_id"] = npc_id
    if player_id:
        query["player_id"] = player_id
    if event_type:
        query["event_type"] = event_type
    if tag:
        # Case-insensitive element match — handles "Hostile" vs "hostile" inconsistency
        query["tags"] = {"$elemMatch": {"$regex": f"^{re.escape(tag)}$", "$options": "i"}}

    cursor = memories_collection.find(query).sort("timestamp", -1)
    return [MemoryOut.model_validate(doc) for doc in cursor]


def update_memory(memory_id: str, data: MemoryUpdate) -> Optional[MemoryOut]:
    oid = _to_object_id(memory_id)
    if oid is None:
        return None

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if updates:
        memories_collection.update_one({"_id": oid}, {"$set": updates})

    doc = memories_collection.find_one({"_id": oid})
    return MemoryOut.model_validate(doc) if doc else None


def upsert_memory(memory_id: str, data: MemoryUpdate) -> Optional[dict]:
    """Update if exists (200) or create with provided fields (201)."""
    oid = _to_object_id(memory_id)
    if oid is None:
        return None

    existing = memories_collection.find_one({"_id": oid})

    updates = {k: v for k, v in data.model_dump().items() if v is not None}

    if existing:
        if updates:
            memories_collection.update_one({"_id": oid}, {"$set": updates})
        doc = memories_collection.find_one({"_id": oid})
        return {"memory": MemoryOut.model_validate(doc), "created": False}
    else:
        from datetime import datetime, timezone
        new_doc = {"_id": oid, "npc_id": "unknown", "timestamp": datetime.now(timezone.utc), **updates}
        memories_collection.insert_one(new_doc)
        doc = memories_collection.find_one({"_id": oid})
        return {"memory": MemoryOut.model_validate(doc), "created": True}


def delete_memory(memory_id: str) -> bool:
    oid = _to_object_id(memory_id)
    if oid is None:
        return False
    result = memories_collection.delete_one({"_id": oid})
    return result.deleted_count == 1
