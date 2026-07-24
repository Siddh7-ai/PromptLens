import os
import json
import pytest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient

from src.proxy.server import app, get_global_store
from src.compress.text_compressor import get_token_count

client = TestClient(app)
store = get_global_store()


def test_real_agent_multiturn_integration():
    """
    End-to-end test simulating a multi-turn AI agent executing a coding task:
    1. Agent receives large pytest failure output.
    2. Proxy compresses tool output and injects retrieve_original tool.
    3. Agent invokes retrieve_original(id=...) to fetch raw trace.
    4. Proxy substitutes full original content accurately.
    """
    fixture_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "python_stack_trace.log"))
    with open(fixture_path, "r", encoding="utf-8") as f:
        large_log = f.read()

    # --- Turn 1: Agent receives compressed tool output ---
    turn1_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "tools": [
            {"name": "bash", "description": "Execute bash", "input_schema": {"type": "object"}}
        ],
        "messages": [
            {"role": "user", "content": "Run tests"},
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "toolu_1", "name": "bash", "input": {"cmd": "pytest"}}]
            },
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": large_log}]
            }
        ]
    }

    mock_resp_1 = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=b'{"id": "resp_1", "role": "assistant", "content": [{"type": "text", "text": "Need full trace."}]}'
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp_1

        response = client.post("/v1/messages", json=turn1_payload)
        assert response.status_code == 200

        called_req = mock_send.call_args[0][0]
        upstream_payload_1 = json.loads(called_req.content)

        # Verify tool output was compressed and banner added
        tool_res = upstream_payload_1["messages"][2]["content"][0]["content"]
        assert len(tool_res) < len(large_log)
        assert "Original ID:" in tool_res

        hash_id = tool_res.split("Original ID: ")[1].split(".")[0]
        assert store.has(hash_id)

    # --- Turn 2: Agent calls retrieve_original tool ---
    turn2_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "tools": [
            {"name": "bash", "description": "Execute bash", "input_schema": {"type": "object"}},
            {"name": "retrieve_original", "description": "Retrieve full text", "input_schema": {"type": "object"}}
        ],
        "messages": [
            {"role": "user", "content": "Run tests"},
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "toolu_2", "name": "retrieve_original", "input": {"id": hash_id}}]
            },
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "toolu_2", "content": "fetching..."}]
            }
        ]
    }

    mock_resp_2 = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=b'{"id": "resp_2", "role": "assistant", "content": [{"type": "text", "text": "Task resolved!"}]}'
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp_2

        response = client.post("/v1/messages", json=turn2_payload)
        assert response.status_code == 200

        called_req = mock_send.call_args[0][0]
        upstream_payload_2 = json.loads(called_req.content)

        retrieved = upstream_payload_2["messages"][2]["content"][0]["content"]
        assert retrieved == large_log
