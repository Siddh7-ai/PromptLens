"""
Unit tests for LogCompressor.
Covers: small logs, large logs, repeated logs, logs with exceptions, multiple errors.
"""
import pytest
from src.compress.log_compressor import LogCompressor
from src.store.retrieval_store import RetrievalStore


@pytest.fixture
def store():
    return RetrievalStore(ttl_seconds=3600)


@pytest.fixture
def log_compressor(store):
    return LogCompressor(head_lines=5, tail_lines=5, min_lines_threshold=20, min_tokens_threshold=40, store=store)


def test_small_logs_pass_intact(log_compressor):
    small_log = "2026-07-20 10:00:00 INFO Service started\n2026-07-20 10:00:01 INFO Ready for requests"
    res = log_compressor.compress(small_log)
    assert not res.is_compressed
    assert res.compressed_log == small_log


def test_repeated_consecutive_logs_collapsed(log_compressor):
    lines = [
        "2026-07-20 10:00:00 INFO Connection pool initialized"
    ] + [
        "2026-07-20 10:00:05 DEBUG Heartbeat ping sent to 10.0.0.1" for _ in range(50)
    ] + [
        "2026-07-20 10:05:00 INFO Completed polling cycle"
    ]
    raw_log = "\n".join(lines)
    res = log_compressor.compress(raw_log)

    assert res.is_compressed
    assert "Repeated" in res.compressed_log
    assert res.collapsed_repeats_count > 40
    assert "Connection pool initialized" in res.compressed_log
    assert "Completed polling cycle" in res.compressed_log


def test_logs_with_exception_pinned_in_middle(log_compressor, store):
    lines = [f"2026-07-20 10:00:{i:02d} INFO Step {i}" for i in range(1, 40)]
    # Insert critical exceptions in middle
    lines.insert(20, "2026-07-20 10:00:20 ERROR DatabaseConnectionException: Failed to connect to port 5432")
    lines.insert(25, "2026-07-20 10:00:25 CRITICAL OutOfMemoryError in worker-4")
    raw_log = "\n".join(lines)

    res = log_compressor.compress(raw_log)

    assert res.is_compressed
    assert "DatabaseConnectionException" in res.compressed_log
    assert "OutOfMemoryError" in res.compressed_log
    assert "[PromptLens Pinned Middle Errors/Exceptions]" in res.compressed_log

    # Verify retrieval
    retrieved = store.get(res.retrieval_id)
    assert retrieved == raw_log


def test_configurable_error_keywords():
    custom_compressor = LogCompressor(
        head_lines=5, tail_lines=5, min_lines_threshold=15,
        error_keywords=["MY_CUSTOM_FAULT", "PANIC_CODE_99"]
    )
    lines = [f"Line {i} info" for i in range(30)]
    lines.insert(15, "Line 15: Critical alert MY_CUSTOM_FAULT triggered")
    raw_log = "\n".join(lines)

    res = custom_compressor.compress(raw_log)
    assert res.is_compressed
    assert "MY_CUSTOM_FAULT" in res.compressed_log
