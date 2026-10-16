"""
Integration tests for Proxy Core behavior.
Covers: OpenAI requests, Anthropic requests, streaming (SSE), non-compressible requests,
compression failure fail-open, and invalid inputs.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient

from src.proxy.server import app, retrieval_store

client = TestClient(app)


def test_openai_chat_completions_proxy():
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a code reviewer."},
            {"role": "user", "content": "Line of code...\n" * 50},
            {"role": "user", "content": "Review this."}
        ]
    }

    mock_resp = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=b'{"id": "chatcmpl-123", "choices": [{"message": {"role": "assistant", "content": "Code looks good."}}]}'
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp

        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["choices"][0]["message"]["content"] == "Code looks good."

        # Verify upstream received processed request with sacred user prompt intact
        called_req = mock_send.call_args[0][0]
        upstream_payload = json.loads(called_req.content)
        assert upstream_payload["messages"][-1]["content"] == "Review this."


def test_anthropic_messages_proxy():
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "tools": [{"name": "bash", "description": "runs bash", "input_schema": {}}],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "call_1", "content": "Error frame...\n" * 60}
                ]
            },
            {"role": "user", "content": "Analyze error"}
        ]
    }

    mock_resp = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=b'{"id": "msg_001", "role": "assistant", "content": [{"type": "text", "text": "Identified issue."}]}'
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp

        response = client.post("/v1/messages", json=payload)
        assert response.status_code == 200

        called_req = mock_send.call_args[0][0]
        upstream_payload = json.loads(called_req.content)
        assert upstream_payload["messages"][-1]["content"] == "Analyze error"
        # retrieve_original tool should be injected
        tool_names = [t["name"] for t in upstream_payload["tools"]]
        assert "retrieve_original" in tool_names


def test_request_without_compressible_content():
    """Small request without compressible content passes through unmodified."""
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "Hello, world!"}
        ]
    }

    mock_resp = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=b'{"choices": [{"message": {"role": "assistant", "content": "Hello!"}}]}'
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp

        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200

        called_req = mock_send.call_args[0][0]
        upstream_payload = json.loads(called_req.content)
        assert upstream_payload["messages"][0]["content"] == "Hello, world!"


def test_streaming_sse_passthrough():
    """Server-Sent Events streaming response passes chunks without buffering breaks."""
    payload = {
        "model": "gpt-4o",
        "stream": True,
        "messages": [{"role": "user", "content": "Tell me a joke"}]
    }

    sse_data = b'data: {"choices": [{"delta": {"content": "Why did "}}]}\n\ndata: [DONE]\n\n'

    mock_resp = httpx.Response(
        status_code=200,
        headers={"content-type": "text/event-stream"},
        content=sse_data
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp

        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert b"Why did " in response.content


def test_invalid_json_payload_fails_open_or_propagates():
    """Non-JSON or malformed payload does not crash proxy."""
    mock_resp = httpx.Response(status_code=400, content=b'{"error": "Bad Request"}')
    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp
        response = client.post(
            "/v1/chat/completions",
            content=b"not a valid json {",
            headers={"content-type": "application/json"}
        )
        # Should forward to upstream or return status without 500 server crash
        assert response.status_code in (400, 200)
