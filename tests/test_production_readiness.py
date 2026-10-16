import os
import json
import tempfile
import pytest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient

from src.store.retrieval_store import RetrievalStore
from src.proxy.server import app, MAX_PAYLOAD_BYTES
from src.utils.token_utils import get_token_count

client = TestClient(app)


def test_sqlite_persistence_across_reboots():
    """Verify that vault items saved in SQLite survive store re-instantiations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_vault.db")
        
        # Session 1: save payload to SQLite store
        store_1 = RetrievalStore(ttl_seconds=3600, db_path=db_path)
        payload = "def process_transaction(user_id: str):\n    return {'status': 'processed', 'user': user_id}"
        retrieval_id = store_1.save(payload)
        
        assert len(retrieval_id) == 12
        assert store_1.has(retrieval_id) is True
        del store_1  # Simulate process shutdown
        
        # Session 2: new store instance pointing to same SQLite database
        store_2 = RetrievalStore(ttl_seconds=3600, db_path=db_path)
        assert store_2.has(retrieval_id) is True
        retrieved = store_2.get(retrieval_id)
        assert retrieved == payload
        
        # Line slicing on recovered data
        sliced = store_2.retrieve_original(retrieval_id, start_line=1, end_line=1)
        assert "process_transaction" in sliced


def test_token_utils_handles_special_tokens_safely():
    """Verify tiktoken tokenizer does not throw ValueError on disallowed special tokens."""
    special_text = "The model encountered <|endoftext|> and <|im_start|> tokens in log."
    tokens = get_token_count(special_text)
    assert tokens > 0
    assert isinstance(tokens, int)


def test_health_telemetry_deep_structure():
    """Verify production /health and /ready endpoints return complete operational telemetry."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["healthy"] is True
    assert "version" in data
    assert "uptime_seconds" in data
    assert "vault" in data
    assert "backend" in data["vault"]
    assert "metrics" in data
    assert "security" in data
    assert data["security"]["ssl_verify"] is True

    # Check /ready and /healthz aliases
    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ok"


def test_payload_size_limit_guardrail():
    """Verify middleware rejects oversized payloads with HTTP 413."""
    oversized_headers = {
        "content-length": str(MAX_PAYLOAD_BYTES + 1024),
        "content-type": "application/json"
    }
    resp = client.post("/v1/messages", content=b"{}", headers=oversized_headers)
    assert resp.status_code == 413
    assert "Payload Too Large" in resp.json()["error"]


def test_control_plane_authentication():
    """Verify sensitive admin endpoints require PROMPTLENS_API_KEY when configured."""
    with patch.dict(os.environ, {"PROMPTLENS_API_KEY": "secret-admin-token-123"}):
        # 1. Unauthorized request
        resp_unauth = client.post("/api/vault/clear")
        assert resp_unauth.status_code == 401
        assert "Unauthorized" in resp_unauth.json()["error"]

        # 2. Authorized via x-api-key header
        resp_auth = client.post("/api/vault/clear", headers={"x-api-key": "secret-admin-token-123"})
        assert resp_auth.status_code == 200
        assert resp_auth.json()["status"] == "cleared"

        # 3. Authorized via Bearer token
        resp_bearer = client.post("/api/vault/clear", headers={"authorization": "Bearer secret-admin-token-123"})
        assert resp_bearer.status_code == 200


def test_format_accurate_offline_fallback():
    """Verify offline mock returns OpenAI choices for OpenAI route and Anthropic content for Anthropic route."""
    mock_401 = httpx.Response(status_code=401, content=b'{"error": "Unauthorized"}')
    
    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_401

        # 1. OpenAI chat completions fallback
        openai_req = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "ping"}]
        }
        resp_openai = client.post("/v1/chat/completions", json=openai_req)
        assert resp_openai.status_code == 200
        data_openai = resp_openai.json()
        assert "choices" in data_openai
        assert data_openai["choices"][0]["message"]["role"] == "assistant"
        assert data_openai["object"] == "chat.completion"

        # 2. Anthropic messages fallback
        anthropic_req = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [{"role": "user", "content": "ping"}]
        }
        resp_anthropic = client.post("/v1/messages", json=anthropic_req)
        assert resp_anthropic.status_code == 200
        data_anthropic = resp_anthropic.json()
        assert "content" in data_anthropic
        assert data_anthropic["type"] == "message"
        assert data_anthropic["role"] == "assistant"
