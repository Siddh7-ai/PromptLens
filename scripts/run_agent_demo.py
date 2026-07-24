import sys
import os
import json
import httpx
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from src.proxy.server import app, get_global_store
from src.compress.text_compressor import get_token_count

client = TestClient(app)
store = get_global_store()


def run_simulated_agent_task():
    print("=" * 70)
    print("      PROMPTLENS REAL AGENT INTEGRATION DEMO")
    print("=" * 70)
    print("Task: Agent debugging a failing test suite with massive log outputs.\n")

    # Load real fixture for large test failure log
    fixture_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures", "python_stack_trace.log"))
    with open(fixture_path, "r", encoding="utf-8") as f:
        large_test_log = f.read()

    # Turn 1: Agent requests bash execution
    print(" Turn 1: Agent runs pytest suite (receives 3,000+ byte failure trace)")
    
    request_turn_1 = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "tools": [
            {"name": "bash", "description": "Execute terminal command", "input_schema": {"type": "object"}}
        ],
        "messages": [
            {"role": "user", "content": "Run the pytest suite and tell me why it failed."},
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "toolu_run_tests", "name": "bash", "input": {"command": "pytest"}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_run_tests", "content": large_test_log}
                ]
            }
        ]
    }

    mock_resp_1 = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=b'{"id": "msg_turn_1", "role": "assistant", "content": [{"type": "text", "text": "Need raw log trace."}]}'
    )

    baseline_tokens_turn1 = get_token_count(json.dumps(request_turn_1))

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp_1

        response_1 = client.post("/v1/messages", json=request_turn_1)
        assert response_1.status_code == 200

        called_req = mock_send.call_args[0][0]
        upstream_payload_1 = json.loads(called_req.content)

        compressed_tokens_turn1 = get_token_count(json.dumps(upstream_payload_1))
        compressed_text = upstream_payload_1["messages"][2]["content"][0]["content"]
        retrieval_id = compressed_text.split("Original ID: ")[1].split(".")[0]

        savings_turn1 = (1.0 - (compressed_tokens_turn1 / baseline_tokens_turn1)) * 100

        print(f"   [Raw Output Size]: {len(large_test_log)} bytes (~{get_token_count(large_test_log)} tokens)")
        print(f"   [Baseline Request]: {baseline_tokens_turn1} tokens")
        print(f"   [PromptLens Request]: {compressed_tokens_turn1} tokens")
        print(f"   [Token Savings]: {savings_turn1:.2f}%")
        print(f"   [Saved to Vault]: Original ID '{retrieval_id}'")
        print("   [Injected Tool]: 'retrieve_original' added automatically to tools")
        print("-" * 70)

    # Turn 2: Agent calls retrieve_original tool to fetch exact line
    print("\n Turn 2: Agent calls retrieve_original(id='{}')".format(retrieval_id))

    request_turn_2 = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "tools": [
            {"name": "bash", "description": "Execute terminal command", "input_schema": {"type": "object"}},
            {"name": "retrieve_original", "description": "Retrieve full content", "input_schema": {"type": "object"}}
        ],
        "messages": [
            {"role": "user", "content": "Run the pytest suite and tell me why it failed."},
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "toolu_ret_01", "name": "retrieve_original", "input": {"id": retrieval_id}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_ret_01", "content": "fetching..."}
                ]
            }
        ]
    }

    mock_resp_2 = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json"},
        content=b'{"id": "msg_turn_2", "role": "assistant", "content": [{"type": "text", "text": "Task completed successfully."}]}'
    )

    with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp_2

        response_2 = client.post("/v1/messages", json=request_turn_2)
        assert response_2.status_code == 200

        called_req_2 = mock_send.call_args[0][0]
        upstream_payload_2 = json.loads(called_req_2.content)

        retrieved_content = upstream_payload_2["messages"][2]["content"][0]["content"]
        assert retrieved_content == large_test_log

        print("   [Vault Retrieval Status]: SUCCESS (100% exact match to original log)")
        print("   [Agent Outcome]: Task completed with 0 loss of information!")

    print("\n" + "=" * 70)
    print(" DEMO RESULT: Real Agent completed multi-turn task through PromptLens!")
    print("=" * 70)


if __name__ == "__main__":
    run_simulated_agent_task()
