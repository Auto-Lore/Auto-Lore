from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.models.memory_models import MemoryCreate, MemoryOut, MemoryUpdate
from app.services import memory_service

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("", response_model=MemoryOut, status_code=201)
def create_memory(memory: MemoryCreate):
    return memory_service.create_memory(memory)


@router.get("", response_model=List[MemoryOut])
def get_memories(
    npc_id: Optional[str] = None,
    player_id: Optional[str] = None,
    event_type: Optional[str] = None,
    tag: Optional[str] = None,
):
    return memory_service.get_memories(npc_id, player_id, event_type, tag)


@router.put("/{memory_id}", response_model=MemoryOut)
def update_memory(memory_id: str, memory: MemoryUpdate):
    updated = memory_service.update_memory(memory_id, memory)
    if updated is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return updated


@router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: str):
    deleted = memory_service.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
