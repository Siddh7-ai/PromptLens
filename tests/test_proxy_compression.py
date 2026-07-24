import json
import pytest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient

from src.proxy.server import app
from src.store.retrieval_store import get_global_store

retrieval_store = get_global_store()
client = TestClient(app)


def test_tool_result_compression_and_tool_injection():
    """
    Test that incoming tool_result in POST /v1/messages is compressed,
    stored in retrieval_store, and retrieve_original tool is injected.
    """
    # Create large tool output (>150 tokens, >300 bytes)
    large_log_output = "\n".join([f"Line {i}: Executing automated task and processing data..." for i in range(100)])

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "tools": [
            {
                "name": "bash",
                "description": "Execute bash command",
                "input_schema": {"type": "object"}
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01_bash",
                        "content": large_log_output
                    }
                ]
            }
        ]
    }

    mock_upstream_response = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=b'{"id": "msg_resp", "role": "assistant", "content": []}'
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_upstream_response

        response = client.post(
            "/v1/messages",
            headers={"content-type": "application/json"},
            json=payload
        )

        assert response.status_code == 200
        assert mock_send.call_count == 1

        # Inspect the request sent to upstream LLM API
        called_req = mock_send.call_args[0][0]
        upstream_payload = json.loads(called_req.content)

        # 1. Verify retrieve_original tool injection
        tools = upstream_payload["tools"]
        assert len(tools) == 2
        tool_names = [t["name"] for t in tools]
        assert "bash" in tool_names
        assert "retrieve_original" in tool_names

        # 2. Verify tool_result content compression
        msg_content = upstream_payload["messages"][0]["content"][0]
        compressed_text = msg_content["content"]
        assert len(compressed_text) < len(large_log_output)
        assert "[PromptLens: Content compressed" in compressed_text
        assert "Original ID:" in compressed_text

        # 3. Extract hash ID and verify retrieval store entry
        # Extract ID from banner: Original ID: <hash>.
        hash_id = compressed_text.split("Original ID: ")[1].split(".")[0]
        assert retrieval_store.has(hash_id)
        assert retrieval_store.get(hash_id) == large_log_output


def test_retrieve_original_tool_roundtrip():
    """
    Test that when assistant calls retrieve_original(id=hash_id),
    the proxy intercepts tool_result and substitutes full uncompressed text.
    """
    original_secret_text = "SECRET_UNCOMPRESSED_DATA_LINE_1\nLINE 2\nLINE 3\nLINE 4"
    stored_id = retrieval_store.save(original_secret_text)

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "tools": [
            {
                "name": "retrieve_original",
                "description": "Retrieve full uncompressed original content",
                "input_schema": {"type": "object"}
            }
        ],
        "messages": [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_retrieve_99",
                        "name": "retrieve_original",
                        "input": {"id": stored_id}
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_retrieve_99",
                        "content": "fetching..."
                    }
                ]
            }
        ]
    }

    mock_upstream_response = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=b'{"id": "msg_resp_2", "role": "assistant", "content": []}'
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_upstream_response

        response = client.post(
            "/v1/messages",
            headers={"content-type": "application/json"},
            json=payload
        )

        assert response.status_code == 200
        called_req = mock_send.call_args[0][0]
        upstream_payload = json.loads(called_req.content)

        # Verify tool_result content was substituted with original_secret_text
        tool_result_block = upstream_payload["messages"][1]["content"][0]
        assert tool_result_block["content"] == original_secret_text

