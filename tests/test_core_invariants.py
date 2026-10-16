"""
Core Invariant Tests for PromptLens.
Strictly verifies:
- Test 1: User prompt preservation (Original user prompt == forwarded user prompt exactly)
- Test 2: Error preservation (Critical errors remain in compressed content)
- Test 3: Request validity (OpenAI and Anthropic request structures remain valid)
- Test 4: Fail-open guarantee (If compression raises error, original request forwarded intact)
- Test 5: Token reduction (Large context actually shrinks)
- Test 6: Reversible retrieval (Compressed content retrievable by ID)
"""
import copy
import json
import pytest
from unittest.mock import patch

from src.proxy.openai import OpenAIHandler
from src.proxy.anthropic import AnthropicHandler
from src.compress.log_compressor import LogCompressor
from src.store.retrieval_store import RetrievalStore
from src.tokens.counter import TokenCounter


@pytest.fixture
def store():
    return RetrievalStore(ttl_seconds=3600)


@pytest.fixture
def counter():
    return TokenCounter()


# ==============================================================================
# TEST 1: User Prompt Preservation
# ==============================================================================
def test_1_user_prompt_preservation_openai(store):
    """The user's actual prompt must NEVER be modified or compressed."""
    handler = OpenAIHandler(store=store)
    user_prompt = "Please fix the authentication bug in login.py where bcrypt verification fails."
    large_history = "INFO log output\n" * 100

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": large_history},
            {"role": "assistant", "content": "Acknowledged."},
            {"role": "user", "content": user_prompt}  # Latest user prompt
        ]
    }

    processed, report = handler.process(payload)
    latest_user_msg = processed["messages"][-1]

    # Invariant: Must match character-for-character
    assert latest_user_msg["role"] == "user"
    assert latest_user_msg["content"] == user_prompt


def test_1_user_prompt_preservation_anthropic(store):
    """The user's actual prompt in Anthropic format must NEVER be modified."""
    handler = AnthropicHandler(store=store)
    user_prompt = "Refactor the database connection pool in db.py to support async queries."
    large_tool_output = "2026-07-20 10:00:00 DEBUG polling db\n" * 100

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "t1", "content": large_tool_output}
                ]
            },
            {"role": "assistant", "content": [{"type": "text", "text": "Tool finished."}]},
            {
                "role": "user",
                "content": [{"type": "text", "text": user_prompt}]  # Latest user prompt
            }
        ]
    }

    processed, report = handler.process(payload)
    latest_text = processed["messages"][-1]["content"][0]["text"]
    assert latest_text == user_prompt


# ==============================================================================
# TEST 2: Error Preservation
# ==============================================================================
def test_2_error_preservation():
    """Important failure indicators and exceptions MUST be preserved in compressed logs."""
    compressor = LogCompressor(head_lines=5, tail_lines=5, min_lines_threshold=15)
    log_lines = [f"2026-07-20 12:00:{i:02d} INFO Background task step {i}" for i in range(40)]
    # Insert critical middle errors
    log_lines.insert(15, "2026-07-20 12:00:15 ERROR DatabaseTimeoutException: Connection to 10.0.0.5 timed out")
    log_lines.insert(25, "2026-07-20 12:00:25 FATAL CrashLoopBackOff: Container healthcheck failed")
    raw_log = "\n".join(log_lines)

    res = compressor.compress(raw_log)
    assert res.is_compressed
    assert "DatabaseTimeoutException" in res.compressed_log
    assert "CrashLoopBackOff" in res.compressed_log


# ==============================================================================
# TEST 3: Request Validity
# ==============================================================================
def test_3_request_validity_openai(store):
    """OpenAI payload must remain structurally valid and well-formed."""
    handler = OpenAIHandler(store=store)
    code_block = """
def compute_metrics(records):
    total = 0
    valid_count = 0
    for r in records:
        if r.get('active'):
            total += r.get('val', 0)
            valid_count += 1
    avg = total / valid_count if valid_count > 0 else 0
    return {'total': total, 'avg': avg}
""" * 5
    payload = {
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 1500,
        "tools": [{"type": "function", "function": {"name": "run_bash", "parameters": {}}}],
        "messages": [
            {"role": "user", "content": code_block},
            {"role": "user", "content": "What does this code do?"}
        ]
    }

    processed, report = handler.process(payload)
    assert "model" in processed
    assert processed["temperature"] == 0.7
    assert processed["max_tokens"] == 1500
    assert isinstance(processed["messages"], list)
    assert all("role" in m and "content" in m for m in processed["messages"])
    # Tool definitions should include retrieve_original
    tool_names = [t["function"]["name"] for t in processed["tools"]]
    assert "run_bash" in tool_names
    assert "retrieve_original" in tool_names


def test_3_request_validity_anthropic(store):
    """Anthropic payload must remain structurally valid and well-formed."""
    handler = AnthropicHandler(store=store)
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2048,
        "system": "You are a software engineer.",
        "tools": [{"name": "read_file", "description": "reads file", "input_schema": {}}],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "u1", "content": "Line of file\n" * 80}
                ]
            },
            {"role": "user", "content": "Analyze the file"}
        ]
    }

    processed, report = handler.process(payload)
    assert processed["model"] == "claude-3-5-sonnet-20241022"
    assert processed["system"] == "You are a software engineer."
    assert isinstance(processed["tools"], list)
    tool_names = [t["name"] for t in processed["tools"]]
    assert "read_file" in tool_names
    assert "retrieve_original" in tool_names


# ==============================================================================
# TEST 4: Fail-Open Architecture
# ==============================================================================
def test_4_fail_open_on_compressor_error(store):
    """If an internal exception occurs during compression, the original request is forwarded untouched."""
    handler = OpenAIHandler(store=store)
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "Large content...\n" * 50},
            {"role": "user", "content": "Summarize this"}
        ]
    }
    raw_snapshot = copy.deepcopy(payload)

    # Force an exception inside the code compressor
    with patch.object(handler.router, "classify_action", side_effect=RuntimeError("Simulated internal crash")):
        processed, report = handler.process(payload)
        # Invariant: Must return payload identical to original snapshot
        assert processed["messages"][0]["content"] == raw_snapshot["messages"][0]["content"]
        assert report.tokens_saved == 0
        assert report.savings_percentage == 0.0


# ==============================================================================
# TEST 5: Token Reduction
# ==============================================================================
def test_5_token_reduction(store, counter):
    """Large contexts must actually become smaller in token count."""
    handler = OpenAIHandler(store=store, token_counter=counter)
    # Generate 1,000-line JSON array
    data = [{"id": i, "user": f"user_{i}", "active": True} for i in range(200)]
    raw_json = json.dumps(data)
    orig_tokens = counter.count_tokens(raw_json)

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": raw_json},
            {"role": "user", "content": "How many users are active?"}
        ]
    }

    processed, report = handler.process(payload)
    assert report.compressed_tokens < orig_tokens
    assert report.tokens_saved > 0
    assert report.savings_percentage > 30.0


# ==============================================================================
# TEST 6: Reversible Vault Retrieval
# ==============================================================================
def test_6_retrieval_of_compressed_content(store):
    """Compressed content must be 100% recoverable from the vault using its ID."""
    handler = OpenAIHandler(store=store)
    original_code = """
class AuthenticationManager:
    def verify(self, token, context):
        if not token:
            return False
        header = token.split('.')[0]
        payload = token.split('.')[1]
        signature = token.split('.')[2]
        claims = json.loads(base64.b64decode(payload))
        if claims.get('exp') < time.time():
            return False
        if claims.get('iss') != 'auth.company.io':
            return False
        user_id = claims.get('sub')
        roles = claims.get('roles', [])
        if 'admin' not in roles:
            return False
        return True
""" * 5

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": original_code},
            {"role": "user", "content": "Check auth"}
        ]
    }

    processed, report = handler.process(payload)
    assert len(report.retrieval_ids) > 0
    rid = report.retrieval_ids[0]

    # Reversible retrieval check
    recovered = store.get(rid)
    assert recovered == original_code
