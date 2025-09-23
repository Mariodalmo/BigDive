import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["KNOWLEDGE_DB_PATH"] = os.path.join(os.getcwd(), "data", "test_knowledge.json")

from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def cleanup_db():
    db_path = os.environ["KNOWLEDGE_DB_PATH"]
    # Ensure the test DB starts clean
    if os.path.exists(db_path):
        os.remove(db_path)
    yield
    # Cleanup after tests
    if os.path.exists(db_path):
        os.remove(db_path)


def test_update_knowledge_happy_path():
    client = TestClient(app)
    payload = {
        "documents": [
            {
                "title": "Regulation (EU) 2025/123",
                "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32025R0123",
                "type": "regulation",
            },
            {
                "title": "Data Act",
                "url": "https://data.europa.eu/act",
                "type": "law",
            },
        ]
    }
    res = client.post("/update_knowledge", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 2
    assert len(body["documents"]) == 2
    for doc in body["documents"]:
        assert doc["status"] == "pending"
        assert doc["id"]
        assert doc["created_at"]
        assert doc["updated_at"]

    # Confirm via GET
    res2 = client.get("/knowledge")
    assert res2.status_code == 200
    all_docs = res2.json()
    assert all_docs["count"] == 2
    assert len(all_docs["documents"]) == 2
    for doc in all_docs["documents"]:
        assert doc["status"] == "pending"


def test_validation_errors():
    client = TestClient(app)
    # Empty title
    payload_bad_title = {
        "documents": [
            {"title": "   ", "url": "https://example.com/doc", "type": "law"}
        ]
    }
    res = client.post("/update_knowledge", json=payload_bad_title)
    assert res.status_code == 422

    # Bad URL
    payload_bad_url = {
        "documents": [
            {"title": "Doc", "url": "notaurl", "type": "regulation"}
        ]
    }
    res2 = client.post("/update_knowledge", json=payload_bad_url)
    assert res2.status_code == 422

    # Bad type
    payload_bad_type = {
        "documents": [
            {"title": "Doc", "url": "https://example.com", "type": "whitepaper"}
        ]
    }
    res3 = client.post("/update_knowledge", json=payload_bad_type)
    assert res3.status_code == 422

