"""
Unit tests for PromptLens Local CCR (Compress-Cache-Retrieve) Store.
"""
import time
import pytest
from src.store.retrieval_store import RetrievalStore


def test_ccr_save_and_retrieve_full():
    store = RetrievalStore(ttl_seconds=1800)
    text = "Line 1: Alpha\nLine 2: Beta\nLine 3: Gamma\nLine 4: Delta"
    
    retrieval_id = store.save(text)
    assert len(retrieval_id) == 12
    assert store.has(retrieval_id) is True

    retrieved = store.get(retrieval_id)
    assert retrieved == text


def test_ccr_targeted_line_slicing():
    store = RetrievalStore(ttl_seconds=1800)
    lines = [f"Line {i}: Data value {i*10}" for i in range(1, 51)]
    full_text = "\n".join(lines)

    retrieval_id = store.save(full_text)
    
    # Retrieve lines 10 to 15
    snippet = store.get(retrieval_id, line_range=[10, 15])
    assert snippet is not None
    assert "Lines 10-15" in snippet
    assert "Line 10:" in snippet
    assert "Line 15:" in snippet
    assert "Line 1:" not in snippet


def test_ccr_regex_and_context_lines():
    store = RetrievalStore(ttl_seconds=1800)
    lines = [
        "2026-08-29 10:00:00 [INFO] System boot",
        "2026-08-29 10:00:01 [INFO] Connected to db",
        "2026-08-29 10:00:02 [ERROR] Database timeout on port 5432",
        "2026-08-29 10:00:03 [INFO] Retrying connection...",
        "2026-08-29 10:00:04 [INFO] Connection recovered"
    ]
    full_text = "\n".join(lines)
    retrieval_id = store.save(full_text)

    # Search for ERROR with 1 context line before and after
    snippet = store.get(retrieval_id, query="Database timeout", context_lines=1)
    assert snippet is not None
    assert "Database timeout" in snippet
    assert "Connected to db" in snippet
    assert "Retrying connection..." in snippet


def test_ccr_ttl_expiration():
    # Short 1-second TTL for testing
    store = RetrievalStore(ttl_seconds=1)
    retrieval_id = store.save("Temporary data that will expire")
    assert store.has(retrieval_id) is True

    # Sleep past TTL
    time.sleep(1.1)
    assert store.get(retrieval_id) is None
    assert store.has(retrieval_id) is False


def test_ccr_lru_eviction():
    # Capacity of 3 items
    store = RetrievalStore(ttl_seconds=1800, max_items=3)
    id1 = store.save("Payload 1")
    time.sleep(0.01)
    id2 = store.save("Payload 2")
    time.sleep(0.01)
    id3 = store.save("Payload 3")

    assert store.size() == 3

    # Access id1 to make it freshly used
    _ = store.get(id1)
    time.sleep(0.01)

    # Adding a 4th item should evict the least recently used item (id2)
    id4 = store.save("Payload 4")
    assert store.size() == 3
    assert store.has(id1) is True
    assert store.has(id3) is True
    assert store.has(id4) is True
    assert store.has(id2) is False


def test_retrieve_original_convenience_alias():
    store = RetrievalStore(ttl_seconds=1800)
    full_text = "\n".join([f"L{i}: content" for i in range(1, 20)])
    retrieval_id = store.save(full_text)

    res = store.retrieve_original(retrieval_id, start_line=5, end_line=8)
    assert res is not None
    assert "Lines 5-8" in res
