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
