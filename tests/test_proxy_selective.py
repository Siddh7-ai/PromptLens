"""
Integration tests for PromptLens Selective Context Optimization Proxy:
Verifies the 5 Non-Negotiable Invariants:
1. User prompt is sacred (never rewritten).
2. Selective optimization only (only large tool outputs/JSON/logs).
3. Zero permanent loss via local CCR.
4. Prefix history preserved untouched.
5. Local resolution of retrieve_original tool calls.
"""
import copy
import json
import pytest
from src.proxy.server import process_anthropic_payload, RETRIEVE_ORIGINAL_TOOL
from src.store.retrieval_store import get_global_store


def test_user_prompt_is_sacred_and_never_modified():
    store = get_global_store()
    raw_user_prompt = "Fix the login bug in src/auth.py and make sure all tests pass."
    
    payload = {
        "model": "claude-3-7-sonnet-20250219",
        "messages": [
            {
                "role": "user",
                "content": raw_user_prompt
            }
        ]
    }
    
    original_copy = copy.deepcopy(payload)
    processed, _ = process_anthropic_payload(payload)

    # Invariant 1: User prompt must be 100% byte-identical
    assert processed["messages"][0]["content"] == raw_user_prompt
    assert processed["messages"][0] == original_copy["messages"][0]


def test_prefix_history_and_system_preserved():
    payload = {
        "model": "claude-3-7-sonnet-20250219",
        "system": "You are an expert Python engineer.",
        "messages": [
            {"role": "user", "content": "Hello, can you help me refactor my backend?"},
            {"role": "assistant", "content": "Certainly! Please share the files or run the test suite."},
            {"role": "user", "content": "Here is the issue."}
        ]
    }

    processed, _ = process_anthropic_payload(payload)
    assert processed["system"] == "You are an expert Python engineer."
    assert processed["messages"][0]["content"] == "Hello, can you help me refactor my backend?"
    assert processed["messages"][1]["content"] == "Certainly! Please share the files or run the test suite."
    assert processed["messages"][2]["content"] == "Here is the issue."


def test_selective_tool_result_compression_and_ccr_vault():
    store = get_global_store()
    
    # 500-line simulated pytest error log
    log_lines = ["============================= test session starts =============================="]
    for i in range(1, 100):
        log_lines.append(f"FAILED tests/test_core.py::test_case_{i} - AssertionError: assert False == True")
        log_lines.append("  Traceback (most recent call last):")
        log_lines.append(f"    File 'tests/test_core.py', line {i*3}, in test_case_{i}")
        log_lines.append("      assert False == True")
    log_lines.append("======================== 99 failed in 4.12s ========================")
    bulk_log_output = "\n".join(log_lines)

    payload = {
        "model": "claude-3-7-sonnet-20250219",
        "tools": [{"name": "bash", "description": "Execute bash command", "input_schema": {"type": "object"}}],
        "messages": [
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "toolu_bash_1", "name": "bash", "input": {"command": "pytest"}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_bash_1", "content": bulk_log_output}
                ]
            }
        ]
    }

    processed, stored_id = process_anthropic_payload(payload)

    # Invariant 2 & 3: Tool result is compressed and vaulted in local CCR
    assert stored_id is not None
    assert store.has(stored_id) is True
    
    tool_res_content = processed["messages"][1]["content"][0]["content"]
    assert "PromptLens: Content compressed" in tool_res_content
    assert stored_id in tool_res_content
    assert len(tool_res_content) < len(bulk_log_output)

    # Invariant 4: retrieve_original tool was injected into the tools array
    tool_names = [t.get("name") for t in processed.get("tools", [])]
    assert "retrieve_original" in tool_names


def test_transparent_local_retrieval_resolution():
    store = get_global_store()
    raw_payload = "Line 1: critical token\nLine 2: secret key\nLine 3: end of payload"
    stored_id = store.save(raw_payload)

    retrieval_request = {
        "model": "claude-3-7-sonnet-20250219",
        "messages": [
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "toolu_ret_1", "name": "retrieve_original", "input": {"id": stored_id, "line_range": [1, 2]}}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "toolu_ret_1", "content": stored_id}
                ]
            }
        ]
    }

    processed, last_id = process_anthropic_payload(retrieval_request)

    # Must resolve from local CCR cache without touching bash/external tools
    retrieved_content = processed["messages"][1]["content"][0]["content"]
    assert "Lines 1-2" in retrieved_content
    assert "Line 1: critical token" in retrieved_content
    assert "Line 2: secret key" in retrieved_content
