"""
Unit tests for Retrieval API.
Covers: POST /api/retrieve, GET /api/retrieve/:id, ID validation, 404 missing handling.
"""
from fastapi.testclient import TestClient
from src.proxy.server import app, retrieval_store

client = TestClient(app)


def test_retrieval_api_save_and_retrieve_post():
    content = "Raw uncompressed payload for retrieval API test."
    stored_id = retrieval_store.save(content)

    resp = client.post("/api/retrieve", json={"id": stored_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == stored_id
    assert data["content"] == content


def test_retrieval_api_get_endpoint():
    content = "Raw content for GET /api/retrieve/:id endpoint."
    stored_id = retrieval_store.save(content)

    resp = client.get(f"/api/retrieve/{stored_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == stored_id
    assert data["content"] == content


def test_retrieval_api_invalid_id_format():
    # Pass an ID with malicious characters or bad length
    resp = client.post("/api/retrieve", json={"id": "../etc/passwd"})
    assert resp.status_code == 400
    assert "Invalid retrieval ID format" in resp.json()["error"]

    resp_get = client.get("/api/retrieve/bad$$$id@@")
    assert resp_get.status_code == 400


def test_retrieval_api_not_found():
    resp = client.post("/api/retrieve", json={"id": "pl_nonexistent999"})
    assert resp.status_code == 404

    resp_get = client.get("/api/retrieve/pl_nonexistent999")
    assert resp_get.status_code == 404
