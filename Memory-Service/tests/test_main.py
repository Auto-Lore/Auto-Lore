from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _fake_doc(**overrides):
    """Build a MongoDB-shaped document for use in mocked find / insert results."""
    doc = {
        "_id": ObjectId(),
        "npc_id": "npc_1",
        "player_id": "player_1",
        "event_type": "dialogue",
        "description": "Met the player at the tavern.",
        "timestamp": datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc),
        "context_metadata": {"location": "tavern"},
        "tags": ["intro"],
    }
    doc.update(overrides)
    return doc


# --- App startup / health -------------------------------------------------

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "memory-service"}


def test_openapi_schema_loads():
    """Proves all routes registered cleanly at startup — no import errors."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/memories" in paths
    assert "/memories/{memory_id}" in paths


# --- POST /memories -------------------------------------------------------

@patch("app.services.memory_service.memories_collection")
def test_create_memory(mock_collection):
    doc = _fake_doc()
    mock_collection.insert_one.return_value = MagicMock(inserted_id=doc["_id"])
    mock_collection.find_one.return_value = doc

    payload = {
        "npc_id": "npc_1",
        "player_id": "player_1",
        "event_type": "dialogue",
        "description": "Met the player at the tavern.",
    }
    response = client.post("/memories", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["memory_id"] == str(doc["_id"])
    assert body["npc_id"] == "npc_1"
    assert "_id" not in body

    written_doc = mock_collection.insert_one.call_args.args[0]
    assert written_doc["npc_id"] == "npc_1"
    assert written_doc["event_type"] == "dialogue"
    assert "timestamp" in written_doc
    assert "_id" not in written_doc


@patch("app.services.memory_service.memories_collection")
def test_create_memory_missing_field(mock_collection):
    response = client.post("/memories", json={})
    assert response.status_code == 422
    mock_collection.insert_one.assert_not_called()


# --- GET /memories --------------------------------------------------------

@patch("app.services.memory_service.memories_collection")
def test_get_memories_no_filters(mock_collection):
    docs = [_fake_doc(), _fake_doc(event_type="combat")]
    cursor = MagicMock()
    cursor.sort.return_value = docs
    mock_collection.find.return_value = cursor

    response = client.get("/memories")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["memory_id"] == str(docs[0]["_id"])
    assert "_id" not in body[0]

    mock_collection.find.assert_called_once_with({})
    cursor.sort.assert_called_once_with("timestamp", -1)


@patch("app.services.memory_service.memories_collection")
def test_get_memories_partial_filter(mock_collection):
    """Only npc_id provided — other filter keys must NOT be in the query."""
    cursor = MagicMock()
    cursor.sort.return_value = [_fake_doc()]
    mock_collection.find.return_value = cursor

    response = client.get("/memories", params={"npc_id": "npc_1"})

    assert response.status_code == 200
    mock_collection.find.assert_called_once_with({"npc_id": "npc_1"})


@patch("app.services.memory_service.memories_collection")
def test_get_memories_all_filters(mock_collection):
    cursor = MagicMock()
    cursor.sort.return_value = [_fake_doc(event_type="combat")]
    mock_collection.find.return_value = cursor

    response = client.get(
        "/memories",
        params={"npc_id": "npc_1", "player_id": "player_1", "event_type": "combat"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    mock_collection.find.assert_called_once_with(
        {"npc_id": "npc_1", "player_id": "player_1", "event_type": "combat"}
    )


@patch("app.services.memory_service.memories_collection")
def test_get_memories_empty(mock_collection):
    cursor = MagicMock()
    cursor.sort.return_value = []
    mock_collection.find.return_value = cursor

    response = client.get("/memories")
    assert response.status_code == 200
    assert response.json() == []


# --- PUT /memories/{memory_id} -------------------------------------------

@patch("app.services.memory_service.memories_collection")
def test_update_memory_invalid_id(mock_collection):
    response = client.put(
        "/memories/not-a-real-id",
        json={"description": "updated"},
    )
    assert response.status_code == 404
    mock_collection.update_one.assert_not_called()


@patch("app.services.memory_service.memories_collection")
def test_update_memory_not_found(mock_collection):
    mock_collection.find_one.return_value = None

    response = client.put(
        f"/memories/{ObjectId()}",
        json={"description": "updated"},
    )
    assert response.status_code == 404


@patch("app.services.memory_service.memories_collection")
def test_update_memory_success(mock_collection):
    doc = _fake_doc(description="updated description")
    mock_collection.update_one.return_value = MagicMock()
    mock_collection.find_one.return_value = doc

    response = client.put(
        f"/memories/{doc['_id']}",
        json={"description": "updated description"},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "updated description"


# --- DELETE /memories/{memory_id} ----------------------------------------

@patch("app.services.memory_service.memories_collection")
def test_delete_memory_success(mock_collection):
    mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

    response = client.delete(f"/memories/{ObjectId()}")
    assert response.status_code == 204


@patch("app.services.memory_service.memories_collection")
def test_delete_memory_not_found(mock_collection):
    mock_collection.delete_one.return_value = MagicMock(deleted_count=0)

    response = client.delete(f"/memories/{ObjectId()}")
    assert response.status_code == 404


@patch("app.services.memory_service.memories_collection")
def test_delete_memory_invalid_id(mock_collection):
    response = client.delete("/memories/not-a-real-id")
    assert response.status_code == 404
    mock_collection.delete_one.assert_not_called()


# --- POST /chat -----------------------------------------------------------

@patch("app.routers.chat.memory_service.get_memories", return_value=[])
@patch("app.routers.chat.ollama")
def test_chat_returns_reply(mock_ollama, _mock_get_memories):
    mock_result = MagicMock()
    mock_result.message.content = "Greetings, traveller."
    mock_ollama.chat.return_value = mock_result

    payload = {
        "npc_id": "warrior_001",
        "player_id": "player_1",
        "transcript": [{"speaker": "player", "text": "Hello"}],
    }
    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    assert response.json()["reply"] == "Greetings, traveller."


@patch("app.routers.chat.memory_service.get_memories", return_value=[])
@patch("app.routers.chat.ollama")
def test_chat_ollama_failure(mock_ollama, _mock_get_memories):
    mock_ollama.chat.side_effect = Exception("connection refused")

    payload = {
        "npc_id": "warrior_001",
        "player_id": "player_1",
        "transcript": [],
    }
    response = client.post("/chat", json=payload)

    assert response.status_code == 502


@patch("app.routers.chat.memory_service.get_memories", return_value=[])
@patch("app.routers.chat.ollama")
def test_chat_empty_reply(mock_ollama, _mock_get_memories):
    mock_result = MagicMock()
    mock_result.message.content = ""
    mock_ollama.chat.return_value = mock_result

    payload = {
        "npc_id": "warrior_001",
        "player_id": "player_1",
        "transcript": [],
    }
    response = client.post("/chat", json=payload)

    assert response.status_code == 502
