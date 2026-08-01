import json
import pytest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient
from src.proxy.server import app

client = TestClient(app)


def test_health_check():
    """Test /health endpoint returns 200 and target_url."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "target_url" in data


def test_proxy_passthrough_success():
    """Test transparent POST request forwarding to upstream LLM API."""
    mock_response_body = b'{"id": "msg_123", "type": "message", "content": [{"type": "text", "text": "Hello world"}]}'
    
    mock_upstream_response = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json", "x-custom-header": "test-value"},
        content=mock_response_body,
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_upstream_response

        response = client.post(
            "/v1/messages",
            headers={
                "x-api-key": "test-api-key",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={"model": "claude-3-5-sonnet", "messages": [{"role": "user", "content": "hi"}]},
        )

        assert response.status_code == 200
        assert response.json() == {"id": "msg_123", "type": "message", "content": [{"type": "text", "text": "Hello world"}]}
        assert response.headers.get("x-custom-header") == "test-value"

        # Verify upstream send was called once
        assert mock_send.call_count == 1
        called_req = mock_send.call_args[0][0]
        assert str(called_req.url) == "https://api.anthropic.com/v1/messages"
        assert called_req.headers.get("x-api-key") == "test-api-key"
        assert called_req.headers.get("anthropic-version") == "2023-06-01"


def test_cors_scoped_origins_allowed():
    """Test that allowed extension domains and dashboard origins receive CORS headers."""
    allowed_origins = [
        "https://chatgpt.com",
        "https://chat.openai.com",
        "https://claude.ai",
        "https://gemini.google.com",
        "https://chat.deepseek.com",
        "https://openrouter.ai",
        "http://localhost:3000",
        "chrome-extension://abcdefghijklmnopqrstuvwxyz123456",
    ]
    for origin in allowed_origins:
        response = client.options("/health", headers={"Origin": origin, "Access-Control-Request-Method": "GET"})
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin


def test_cors_untrusted_origin_blocked():
    """Test that untrusted external origins are blocked by CORS policy."""
    response = client.options("/health", headers={"Origin": "https://malicious-attacker.com", "Access-Control-Request-Method": "GET"})
    assert response.headers.get("access-control-allow-origin") is None


def test_proxy_passthrough_error_propagation():
    """Test that upstream error responses (e.g. 400 Bad Request) are returned intact."""
    mock_error_body = b'{"type": "error", "error": {"type": "invalid_request_error", "message": "Missing model"}}'
    
    mock_upstream_response = httpx.Response(
        status_code=400,
        headers={"content-type": "application/json"},
        content=mock_error_body,
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_upstream_response

        response = client.post(
            "/v1/messages",
            json={},
        )

        assert response.status_code == 400
        assert response.json() == {"type": "error", "error": {"type": "invalid_request_error", "message": "Missing model"}}


def test_settings_api_discipline_mode():
    """Test getting and updating discipline_mode via /api/settings."""
    get_res = client.get("/api/settings")
    assert get_res.status_code == 200
    assert "discipline_mode" in get_res.json()
    assert get_res.json()["discipline_mode"] == "off"

    post_res = client.post(
        "/api/settings",
        json={
            "head_lines": 10,
            "tail_lines": 10,
            "max_json_array": 50,
            "min_tokens_threshold": 100,
            "discipline_mode": "ultra"
        }
    )
    assert post_res.status_code == 200
    assert post_res.json()["settings"]["discipline_mode"] == "ultra"

    # Reset back to off
    client.post(
        "/api/settings",
        json={
            "head_lines": 10,
            "tail_lines": 10,
            "max_json_array": 50,
            "min_tokens_threshold": 100,
            "discipline_mode": "off"
        }
    )


def test_proxy_openai_chat_completions_passthrough():
    """Test POST /v1/chat/completions intercepting payload and relaying response."""
    mock_openai_response_body = json.dumps({
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677858288,
        "model": "gpt-4o",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "The error was caused by a react dependency conflict."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 150,
            "completion_tokens": 12,
            "total_tokens": 162
        }
    }).encode("utf-8")

    mock_upstream_response = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=mock_openai_response_body,
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_upstream_response

        openai_payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a helpful developer assistant."},
                {"role": "user", "content": "Fix error."}
            ]
        }

        response = client.post(
            "/v1/chat/completions",
            json=openai_payload,
            headers={"Authorization": "Bearer sk-testkey"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "chatcmpl-123"
        assert data["choices"][0]["message"]["content"] == "The error was caused by a react dependency conflict."

