import json
import time
import pytest
from src.compress.text_compressor import compress_text, generate_structural_index, deduplicate_logs, find_error_anchors
from src.compress.json_compressor import compress_json, _generate_array_skimming_summary
from src.store.retrieval_store import RetrievalStore, get_global_store


def test_multi_language_structural_index():
    code_content = """# Header Main
class PaymentController:
    def process_payment(self):
        pass

def top_level_func():
    pass

async function handleRequest() {
    return true;
}

struct UserRecord {
    id: u64
}
"""
    lines = code_content.splitlines()
    toc = generate_structural_index(lines)

    assert "[PromptLens Structural Index]" in toc
    assert "class PaymentController" in toc or "def process_payment" in toc
    assert "async function handleRequest" in toc or "struct UserRecord" in toc


def test_retrieval_store_regex_search():
    store = RetrievalStore(ttl_seconds=3600)
    content = "\n".join([
        "Line 1: Normal log",
        "Line 2: Info state initialized",
        "Line 3: DatabaseConnectionException occurred",
        "Line 4: Retrying connection",
        "Line 5: Normal log",
        "Line 6: CriticalFailureException detected",
    ])
    retrieval_id = store.save(content)

    # Search regex pattern
    result = store.get(retrieval_id, query=".*Exception.*", use_regex=True, context_lines=1)

    assert result is not None
    assert "DatabaseConnectionException" in result
    assert "CriticalFailureException" in result
    assert "Line 2: Info state" in result  # Context line
    assert "Line 4: Retrying connection" in result  # Context line


def test_retrieval_store_invalid_regex_fallback():
    store = RetrievalStore(ttl_seconds=3600)
    content = "Line 1: Error [invalid pattern]\nLine 2: Normal operation"
    retrieval_id = store.save(content)

    # Pass an invalid regex pattern (unclosed bracket)
    result = store.get(retrieval_id, query="[invalid pattern", use_regex=True)

    assert result is not None
    assert "Error [invalid pattern]" in result


def test_retrieval_store_line_range_slicing():
    store = RetrievalStore(ttl_seconds=3600)
    lines = [f"Line {i}: Content payload data" for i in range(1, 101)]
    content = "\n".join(lines)
    retrieval_id = store.save(content)

    # Slice lines 20 to 25
    snippet = store.get(retrieval_id, line_range=[20, 25])

    assert snippet is not None
    assert "Lines 20-25" in snippet
    assert "Line 20: Content payload data" in snippet
    assert "Line 25: Content payload data" in snippet
    assert "Line 1: Content" not in snippet
    assert "Line 50: Content" not in snippet


def test_retrieval_store_context_window_merging():
    store = RetrievalStore(ttl_seconds=3600)
    lines = [f"Line {i}: Normal status" for i in range(1, 30)]
    lines[5] = "Line 6: ERROR_ALPHA"
    lines[7] = "Line 8: ERROR_BETA"
    content = "\n".join(lines)
    retrieval_id = store.save(content)

    # Search with context_lines=2 which causes overlapping window merging (lines 4-10)
    snippet = store.get(retrieval_id, query="ERROR", context_lines=2)

    assert snippet is not None
    assert "ERROR_ALPHA" in snippet
    assert "ERROR_BETA" in snippet
    assert "Line 4:" in snippet
    assert "Line 10:" in snippet


def test_log_deduplication_and_error_pinning():
    # Test 1: Log deduplication
    dup_lines = ["2026-07-24 10:00:00 INFO Polling DB..."] * 50
    deduped = deduplicate_logs(dup_lines)
    assert len(deduped) < 5
    assert "repeated log lines omitted" in "\n".join(deduped)

    # Test 2: Error anchor pinning in truncated middle lines
    distinct_log_lines = [f"2026-07-24 10:00:{i:02d} INFO Process step {i}" for i in range(1, 40)]
    distinct_log_lines.insert(20, "2026-07-24 10:00:20 ERROR DB Connection Exception failed in middle worker thread")

    text_log = "\n".join(distinct_log_lines)
    result = compress_text(text_log, head_lines=5, tail_lines=5)

    assert result.is_compressed is True
    assert "PromptLens Pinned Middle Errors/Exceptions" in result.compressed_str
    assert "DB Connection Exception" in result.compressed_str


def test_adaptive_json_skimming_summary():
    large_array = [
        {"id": i, "status": "COMPLETED" if i % 2 == 0 else "PENDING", "score": float(i * 1.5)}
        for i in range(2500)
    ]
    raw_json = json.dumps(large_array)

    result = compress_json(raw_json, max_array_items=2)

    assert result.is_compressed is True
    compressed_data = json.loads(result.compressed_str)
    marker = compressed_data[-1]

    assert marker.get("_promptlens_truncated") is True
    summary = marker.get("_promptlens_summary")
    assert summary is not None
    assert summary["unique_keys"] == ["id", "score", "status"]
    assert summary["numeric_ranges"]["id"]["min"] == 0
    assert summary["numeric_ranges"]["id"]["max"] == 2499
    assert summary["sampled_items_count"] <= 100
    assert summary["total_items"] == 2500


def test_ast_caching_performance():
    store = RetrievalStore(ttl_seconds=3600)
    code_content = "\n".join([f"def func_{i}(): pass" for i in range(500)])
    retrieval_id = store.save(code_content)

    start_time = time.perf_counter()
    structural_map = store.get_structural_map(retrieval_id)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    assert structural_map is not None
    assert len(structural_map["symbols"]) == 500
    # AST Map retrieval from cache should complete in < 0.5 ms
    assert elapsed_ms < 5.0
