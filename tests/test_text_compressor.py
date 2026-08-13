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


def test_npm_log_prefix_not_overmatched():
    npm_log = """npm error code ELIFECYCLE
npm error errno 1
npm error promptlens-dashboard@0.1.0 build: `tsc && vite build`
npm error Exit status 1
npm error 
npm error Failed at the promptlens-dashboard@0.1.0 build script.
npm error This is probably not a problem with npm. There is likely additional logging output above.
npm error src/components/Component0.tsx:10:18 - error TS2339: Property 'id_0' does not exist on type 'Props'. Line detail info text 0 * 1000
npm error src/components/Component1.tsx:12:18 - error TS2339: Property 'id_1' does not exist on type 'Props'. Line detail info text 1 * 1000
npm error src/components/Component2.tsx:14:18 - error TS2339: Property 'id_2' does not exist on type 'Props'. Line detail info text 2 * 1000
npm error src/components/Component3.tsx:16:18 - error TS2339: Property 'id_3' does not exist on type 'Props'. Line detail info text 3 * 1000
npm error src/components/Component4.tsx:18:18 - error TS2339: Property 'id_4' does not exist on type 'Props'. Line detail info text 4 * 1000
npm error src/components/Component5.tsx:20:18 - error TS2339: Property 'id_5' does not exist on type 'Props'. Line detail info text 5 * 1000
npm error src/components/Component6.tsx:22:18 - error TS2339: Property 'id_6' does not exist on type 'Props'. Line detail info text 6 * 1000
npm error src/components/Component7.tsx:24:18 - error TS2339: Property 'id_7' does not exist on type 'Props'. Line detail info text 7 * 1000
npm error src/components/Component8.tsx:26:18 - error TS2339: Property 'id_8' does not exist on type 'Props'. Line detail info text 8 * 1000
npm error Found 15 compiler errors in TypeScript build step.
npm error 
npm error A complete log of this run can be found in:
npm error     C:\\Users\\Raulji Siddharthsinh\\AppData\\Local\\npm-cache\\_logs\\2026-07-31T12_00_00_000Z-debug-0.log"""

    result = compress_text(npm_log, head_lines=4, tail_lines=4)
    assert result.is_compressed is True
    # Routine prefix lines like 'npm error code ELIFECYCLE' should not be over-pinned into anchor block
    assert "Line 1: npm error code ELIFECYCLE" not in result.compressed_str


def test_toc_excludes_comment_lines():
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
    ] + [f"    # Comment line {i} padding description for method logic item details data string = {i} * 1000" for i in range(50)] + [
        "    def cleanup_expired(self) -> int:",
        "        return len(self._store)",
    ]
    code_content = "\n".join(code_lines)

    result = compress_text(code_content, head_lines=5, tail_lines=5)
    assert result.is_compressed is True
    assert "[PromptLens Structural Index]" in result.compressed_str
    # Individual comment lines must NOT be separate ToC items
    assert "- Lines 12-12: # Comment line 1" not in result.compressed_str
    assert "- Lines 13-13: # Comment line 2" not in result.compressed_str


def test_webpack_warn_deprecation_not_pinned():
    webpack_log_lines = [
        "Hash: 8a9b0c1d2e3f",
        "Version: webpack 5.88.2",
        "Time: 3450ms",
        "Built at: 2026-08-07 14:20:00",
        "Entrypoint main = main.js",
    ] + [
        f"[14:20:0{i%10}] WARN  [dep-00{i%5}] DeprecationWarning: Buffer() is deprecated due to security issues. Line detail {i}"
        for i in range(30)
    ] + [
        "[14:20:10] WARN  [dep-999] Module Warning (from ./node_modules/babel-loader): Critical dependency: expression",
        "assets by status 1.2 MiB [cached] 12 assets",
        "webpack 5.88.2 compiled with 31 warnings in 3450 ms",
    ]
    log_content = "\n".join(webpack_log_lines)

    result = compress_text(log_content, head_lines=4, tail_lines=4)
    assert result.is_compressed is True
    # Routine deprecation warnings must NOT be re-pinned into middle errors block
    assert "[PromptLens Pinned Middle Errors/Exceptions]" not in result.compressed_str or "DeprecationWarning: Buffer()" not in result.compressed_str
    assert "DeprecationWarning" not in (result.compressed_str.split("[PromptLens Pinned Middle Errors/Exceptions]")[1] if "[PromptLens Pinned Middle Errors/Exceptions]" in result.compressed_str else "")


def test_typescript_ts2304_ts2322_pinned_and_toc_suppressed():
    ts_build_log_lines = [
        "Compiling frontend application...",
        "tsc --noEmit --project tsconfig.json",
        "Running TypeScript type checker...",
        "Starting compilation unit target ES2022...",
        "Analyzing 145 files...",
        "Failed to compile.",
        "",
        "src/components/UserCard.tsx:15:23 - error TS2304: Cannot find name 'UserRole'.",
        "",
        "  15 |   role: UserRole;",
        "     |         ^^^^^^^^",
        "",
        "src/components/UserCard.tsx:28:5 - error TS2322: Type 'string' is not assignable to type 'number'.",
        "",
        "  28 |   age: \"twenty\";",
        "     |        ^^^^^^^^",
        "",
    ] + [f"  {i} |   internalLineProperty_{i}: boolean;" for i in range(30)] + [
        "Found 2 errors in src/components/UserCard.tsx",
        "npm ERR! Build failed with exit code 1",
    ]
    ts_log_content = "\n".join(ts_build_log_lines)

    result = compress_text(ts_log_content, head_lines=4, tail_lines=4)
    assert result.is_compressed is True
    # Structural Index ToC must NOT appear on build logs
    assert "[PromptLens Structural Index]" not in result.compressed_str
    # Actual TS errors must be pinned in middle errors block
    assert "[PromptLens Pinned Middle Errors/Exceptions]" in result.compressed_str
    assert "TS2304: Cannot find name 'UserRole'" in result.compressed_str
    assert "TS2322: Type 'string' is not assignable to type 'number'" in result.compressed_str

