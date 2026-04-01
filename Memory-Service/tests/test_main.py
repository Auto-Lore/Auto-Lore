from unittest.mock import MagicMock, patch
from bson import ObjectId
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("main.memories_collection")
def test_create_memory(mock_collection):
    fake_id = ObjectId()
    mock_collection.insert_one.return_value = MagicMock(inserted_id=fake_id)

    payload = {"npcId": "npc_1", "playerId": "player_1", "text": "Hello there"}
    response = client.post("/memories", json=payload)

    assert response.status_code == 200
    assert response.json() == {"inserted_id": str(fake_id)}
    mock_collection.insert_one.assert_called_once_with(payload)


@patch("main.memories_collection")
def test_create_memory_missing_field(mock_collection):
    response = client.post("/memories", json={"npcId": "npc_1"})
    assert response.status_code == 422


@patch("main.memories_collection")
def test_search_memories(mock_collection):
    fake_id = ObjectId()
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = [
        {"_id": fake_id, "npcId": "npc_1", "playerId": "player_1", "text": "Hi"}
    ]
    mock_collection.find.return_value = mock_cursor

    payload = {"npcId": "npc_1", "playerId": "player_1"}
    response = client.post("/memories/search", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(fake_id)
    assert data["items"][0]["text"] == "Hi"
    mock_collection.find.assert_called_once_with(
        {"npcId": "npc_1", "playerId": "player_1"}
    )


@patch("main.memories_collection")
def test_search_memories_empty(mock_collection):
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = []
    mock_collection.find.return_value = mock_cursor

    payload = {"npcId": "npc_99", "playerId": "player_99"}
    response = client.post("/memories/search", json=payload)

    assert response.status_code == 200
    assert response.json() == {"items": []}
