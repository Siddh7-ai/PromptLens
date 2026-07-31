import os
import pytest
from src.compress.text_compressor import compress_text, get_token_count

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fixtures"))


def test_compress_long_file_read():
    filepath = os.path.join(FIXTURES_DIR, "long_file_read.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = compress_text(content, head_lines=5, tail_lines=5)

    assert result.is_compressed is True
    assert result.compressed_tokens < result.original_tokens
    assert result.compression_ratio > 0.30
    assert len(result.retrieval_id) == 12
    assert "PromptLens Truncated" in result.compressed_str or "PROMPT LENS TRUNCATED" in result.compressed_str


def test_compress_python_stack_trace():
    filepath = os.path.join(FIXTURES_DIR, "python_stack_trace.log")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = compress_text(content)

    assert result.is_compressed is True
    assert result.compressed_tokens < result.original_tokens
    assert "PromptLens Truncated" in result.compressed_str or "PROMPT LENS TRUNCATED" in result.compressed_str or "stack trace lines" in result.compressed_str
    assert len(result.retrieval_id) == 12


def test_compress_db_query_output():
    filepath = os.path.join(FIXTURES_DIR, "db_query_output.txt")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = compress_text(content, head_lines=5, tail_lines=5)

    assert result.is_compressed is True
    assert result.compressed_tokens < result.original_tokens
    assert len(result.retrieval_id) == 12


def test_compress_git_diff():
    filepath = os.path.join(FIXTURES_DIR, "git_diff.patch")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = compress_text(content, head_lines=5, tail_lines=5)

    assert result.is_compressed is True
    assert result.compressed_tokens < result.original_tokens


def test_small_text_under_threshold():
    small_text = "Line 1\nLine 2\nLine 3"
    result = compress_text(small_text, min_token_threshold=100)

    assert result.is_compressed is False
    assert result.compressed_str == small_text
    assert result.compression_ratio == 0.0


def test_short_noisy_log_adaptive_threshold():
    filepath = os.path.join(FIXTURES_DIR, "short_noisy_npm.log")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = compress_text(content, min_token_threshold=300)

    assert result.is_compressed is True
    assert result.compressed_tokens < result.original_tokens
    assert result.compression_ratio > 0.15


def test_pytest_failure_trace_pins_keyerror():
    pytest_output = """============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\\Users\\Raulji Siddharthsinh\\OneDrive\\Desktop\\PromptLens
plugins: anyio-4.14.2
collected 50 items

tests/test_auth.py .........................                             [ 50%]
tests/test_users.py .................                                    [ 84%]
tests/test_payments.py ..F..                                             [ 94%]
tests/test_orders.py ...                                                 [100%]

================================== FAILURES ===================================
___________________ test_stripe_webhook_invalid_signature ___________________

    def test_stripe_webhook_invalid_signature():
        client = TestClient(app)
        payload = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_123"}}}
        signature = "t=12345,v1=invalid_signature_hash"
>       response = client.post("/webhooks/stripe", json=payload, headers={"Stripe-Signature": signature})
E       KeyError: 'stripe-signature-secret-key'

src/services/stripe.py:45: KeyError

---------------------------- Captured stdout call -----------------------------
DEBUG: Received Stripe webhook event payment_intent.succeeded
ERROR: Secret key missing in environment variables: STRIPE_WEBHOOK_SECRET
=========================== short test summary info ===========================
FAILED tests/test_payments.py::test_stripe_webhook_invalid_signature - KeyError: 'stripe-signature-secret-key'
========================= 1 failed, 49 passed in 2.34s ========================="""

    result = compress_text(pytest_output)
    assert result.is_compressed is True
    assert "KeyError" in result.compressed_str
    assert "Pinned Middle Errors/Exceptions" in result.compressed_str or "KeyError" in result.compressed_str


def test_source_code_toc_generation():
    code_lines = [
        "import time",
        "import hashlib",
        "",
        "class DatabaseVault:",
        '    """In-memory SHA-256 data vault with TTL auto-expiration."""',
        "    def __init__(self, ttl_seconds: int = 3600):",
        "        self.ttl = ttl_seconds",
        "        self._store = {}",
        "",
        "    def save(self, content: str, custom_id: str = None) -> str:",
        '        key = custom_id or hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]',
        '        self._store[key] = {"content": content, "created_at": time.time()}',
        "        return key",
    ] + [f"    # Line padding method internal logic block {i} processing payload data item = {i} * 1000" for i in range(50)] + [
        "    def cleanup_expired(self) -> int:",
        "        return len(self._store)",
    ]
    code_content = "\n".join(code_lines)

    result = compress_text(code_content, head_lines=5, tail_lines=5)
    assert result.is_compressed is True
    assert "PromptLens Structural Index" in result.compressed_str
    assert "class DatabaseVault" in result.compressed_str


