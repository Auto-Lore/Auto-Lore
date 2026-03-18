from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient

app = FastAPI()

client = MongoClient("mongodb://localhost:27017")
db = client["autolore"]
memories_collection = db["memories"]


class MemoryCreate(BaseModel):
    npcId: str
    playerId: str
    text: str


class MemoryResponse(BaseModel):
    inserted_id: str


class MemorySearchRequest(BaseModel):
    npcId: str
    playerId: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/memories", response_model=MemoryResponse)
def create_memory(memory: MemoryCreate):
    document = memory.model_dump()
    result = memories_collection.insert_one(document)
    return MemoryResponse(inserted_id=str(result.inserted_id))


@app.post("/memories/search")
def search_memories(request: MemorySearchRequest):
    cursor = memories_collection.find(
        {"npcId": request.npcId, "playerId": request.playerId}
    ).sort("_id", -1).limit(5)

    items = []
    for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        items.append(doc)

    return {"items": items}
